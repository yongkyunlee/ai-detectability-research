"""AI-detection scoring for GPTZero and Originality.ai.

Provides a non-interactive workflow:

1. :func:`create_detection_template` writes a CSV with one row per text.
   The user fills in ``gptzero_generated_prob`` and ``originality_ai_score``
   columns after running each text through the respective web UIs.

2. :func:`load_detection_from_csv` reads the filled-in CSV and returns
   :class:`DetectionResult` objects ready for analysis.

Parsing helpers remain for backwards compatibility with any stored results.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from ai_text_quality.models import DetectionResult, GeneratedText

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Non-interactive template workflow
# ---------------------------------------------------------------------------

def create_detection_template(
    texts: list[GeneratedText],
    output_path: Path,
) -> Path:
    """Write a CSV template for manual AI-detection scoring.

    Each row identifies a text and has empty score columns for the user to
    fill in after pasting the text into GPTZero / Originality.ai.

    Columns
    -------
    task_id, condition, run_id, model, word_target,
    gptzero_generated_prob, originality_ai_score

    Both score columns should be filled with values between 0 and 1.
    Human probabilities are derived automatically (1 - score).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "task_id",
        "condition",
        "run_id",
        "model",
        "word_target",
        "gptzero_generated_prob",
        "originality_ai_score",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for gen in texts:
            writer.writerow({
                "task_id": gen.task_id,
                "condition": gen.condition,
                "run_id": gen.run_id,
                "model": gen.model,
                "word_target": gen.word_target,
                "gptzero_generated_prob": "",
                "originality_ai_score": "",
            })

    print(f"Wrote detection template with {len(texts)} rows → {output_path}")
    return output_path


def load_detection_from_csv(csv_path: Path) -> list[DetectionResult]:
    """Read a filled-in detection CSV and return DetectionResult objects.

    Rows where both score columns are still empty are skipped.
    """
    results: list[DetectionResult] = []
    skipped = 0

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gptzero_raw = row.get("gptzero_generated_prob", "").strip()
            originality_raw = row.get("originality_ai_score", "").strip()

            if not gptzero_raw and not originality_raw:
                skipped += 1
                continue

            gptzero_gen = float(gptzero_raw) if gptzero_raw else 0.0
            originality_ai = float(originality_raw) if originality_raw else 0.0

            results.append(DetectionResult(
                task_id=row["task_id"],
                condition=row["condition"],
                run_id=row["run_id"],
                model=row.get("model", ""),
                word_target=row.get("word_target", ""),
                gptzero_human_prob=1.0 - gptzero_gen,
                gptzero_generated_prob=gptzero_gen,
                originality_ai_score=originality_ai,
                originality_human_score=1.0 - originality_ai,
            ))

    if skipped:
        print(f"Skipped {skipped} rows with no scores filled in")
    print(f"Loaded {len(results)} detection results from {csv_path}")
    return results


# ---------------------------------------------------------------------------
# Result parsing (kept for loading previously saved results)
# ---------------------------------------------------------------------------

def parse_gptzero_result(
    response: dict,
    task_id: str,
    condition: str,
    run_id: str,
) -> DetectionResult:
    """Parse a GPTZero API response into a :class:`DetectionResult`.

    Extracts probability scores from ``documents[0]`` and per-sentence
    classifications when available.
    """
    doc = response.get("documents", [{}])[0] if response.get("documents") else {}

    human_prob = doc.get("completely_generated_prob", 0.0)
    # GPTZero returns completely_generated_prob as the probability the text
    # is AI-generated.  We store it and derive human_prob = 1 - generated.
    generated_prob = doc.get("completely_generated_prob", 0.0)
    mixed_prob = doc.get("mixed_prob", 0.0)
    # Human probability: what remains after generated + mixed
    human_prob = max(0.0, 1.0 - generated_prob - mixed_prob)

    sentences: list[dict] = []
    for sent in doc.get("sentences", []):
        sentences.append({
            "sentence": sent.get("sentence", ""),
            "generated_prob": sent.get("generated_prob", 0.0),
            "perplexity": sent.get("perplexity", 0.0),
        })

    return DetectionResult(
        task_id=task_id,
        condition=condition,
        run_id=run_id,
        gptzero_human_prob=human_prob,
        gptzero_mixed_prob=mixed_prob,
        gptzero_generated_prob=generated_prob,
        gptzero_sentences=sentences,
    )


def parse_originality_result(
    response: dict,
    detection_result: DetectionResult,
) -> DetectionResult:
    """Update an existing :class:`DetectionResult` with Originality.ai scores.

    Extracts ``score.ai`` and ``score.original`` as well as per-paragraph
    breakdowns when present.
    """
    score = response.get("score", {})
    ai_score = score.get("ai", 0.0)
    human_score = score.get("original", 0.0)

    paragraphs: list[dict] = []
    for para in response.get("paragraphs", []):
        paragraphs.append({
            "text": para.get("text", ""),
            "ai_score": para.get("score", {}).get("ai", 0.0),
            "human_score": para.get("score", {}).get("original", 0.0),
        })

    return detection_result.model_copy(
        update={
            "originality_ai_score": ai_score,
            "originality_human_score": human_score,
            "originality_paragraphs": paragraphs,
        },
    )


# ---------------------------------------------------------------------------
# Batch detection
# ---------------------------------------------------------------------------

def run_detection(
    texts: list[GeneratedText],
) -> list[DetectionResult]:
    """Run interactive detection for both GPTZero and Originality.ai on every text.

    For each text, prints it so the user can paste it into the respective
    web UIs, then collects the reported scores.

    Parameters
    ----------
    texts:
        Generated text objects to analyse.

    Returns
    -------
    list[DetectionResult]
        One result per text.
    """
    results: list[DetectionResult] = []

    for idx, gen_text in enumerate(texts):
        print(
            f"\n[{idx + 1}/{len(texts)}] task={gen_text.task_id} "
            f"condition={gen_text.condition} run={gen_text.run_id}"
        )

        # -- GPTZero ---------------------------------------------------------
        detection = _prompt_gptzero_scores(
            gen_text.text,
            gen_text.task_id,
            gen_text.condition,
            gen_text.run_id,
        )

        # -- Originality.ai --------------------------------------------------
        detection = _prompt_originality_scores(gen_text.text, detection)

        results.append(detection)

    logger.info("Detection complete: %d results produced", len(results))
    return results
