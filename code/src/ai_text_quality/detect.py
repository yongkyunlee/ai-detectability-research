"""AI-detection via manual UI interaction with GPTZero and Originality.ai.

Instead of calling APIs directly, this module prints the text for the user
to paste into the GPTZero and Originality.ai web UIs, then prompts the user
to enter the scores reported by each tool.

Parsing helpers remain for backwards compatibility with any stored results.
:func:`run_detection` orchestrates the interactive workflow over a batch of
:class:`GeneratedText` items.
"""

from __future__ import annotations

import logging

from ai_text_quality.models import DetectionResult, GeneratedText

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Interactive detection helpers
# ---------------------------------------------------------------------------

def _prompt_gptzero_scores(
    text: str,
    task_id: str,
    condition: str,
    run_id: str,
) -> DetectionResult:
    """Print text for the user to paste into GPTZero UI, then collect scores.

    The user should:
    1. Go to https://gptzero.me
    2. Paste the text shown below
    3. Enter the reported scores back here
    """
    separator = "=" * 70
    print(f"\n{separator}")
    print(f"GPTZero - task={task_id} condition={condition} run={run_id}")
    print(f"{separator}")
    print("Paste the following text into https://gptzero.me :")
    print(f"{separator}")
    print(text)
    print(f"{separator}")
    print()

    generated_prob = _read_float("GPTZero AI-generated probability (0-1): ")
    human_prob = 1.0 - generated_prob

    return DetectionResult(
        task_id=task_id,
        condition=condition,
        run_id=run_id,
        gptzero_human_prob=human_prob,
        gptzero_generated_prob=generated_prob,
    )


def _prompt_originality_scores(
    text: str,
    detection_result: DetectionResult,
) -> DetectionResult:
    """Print text for the user to paste into Originality.ai UI, then collect scores.

    The user should:
    1. Go to https://originality.ai
    2. Paste the text shown below
    3. Enter the reported scores back here
    """
    separator = "=" * 70
    print(f"\n{separator}")
    print(
        f"Originality.ai - task={detection_result.task_id} "
        f"condition={detection_result.condition} run={detection_result.run_id}"
    )
    print(f"{separator}")
    print("Paste the following text into https://originality.ai :")
    print(f"{separator}")
    print(text)
    print(f"{separator}")
    print()

    ai_score = _read_float("Originality.ai AI score (0-1): ")
    human_score = 1.0 - ai_score

    return detection_result.model_copy(
        update={
            "originality_ai_score": ai_score,
            "originality_human_score": human_score,
        },
    )


def _read_float(prompt: str) -> float:
    """Read a float value from stdin with validation."""
    while True:
        try:
            value = float(input(prompt))
            if 0.0 <= value <= 1.0:
                return value
            print("  Value must be between 0 and 1. Try again.")
        except ValueError:
            print("  Invalid number. Try again.")


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
