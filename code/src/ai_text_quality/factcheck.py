"""Factual accuracy checking via claim extraction and verification.

Instead of matching against a pre-defined gold fact table, this module:
1. Extracts atomic factual claims from generated text (via LLM)
2. Verifies each claim against reference documentation (via LLM)
3. Computes factual precision = correct / (correct + incorrect)

Supports two workflows:
- Interactive: prompts printed for stdin-based copy/paste (legacy)
- File-based: prompts saved to .txt files; CLI tool saves output to disk
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

from ai_text_quality.io_utils import write_grouped_prompts
from ai_text_quality.models import Claim, ClaimVerdict, FactCheckResult, GeneratedText, Task
from ai_text_quality.paths import FACTUAL_DIR, PROMPTS_DIR, ROOT_DIR


# ---------------------------------------------------------------------------
# Step 1: Claim extraction
# ---------------------------------------------------------------------------

_EXTRACT_SYSTEM = (
    "You are a fact-checking assistant. Extract all atomic factual claims "
    "from the given text. A factual claim is a statement that can be verified "
    "as true or false against documentation — e.g., version numbers, commands, "
    "file names, configuration details, behavioral descriptions, compatibility "
    "statements. Exclude opinions, subjective assessments, and hedged statements."
)

_EXTRACT_USER_TEMPLATE = """Text to analyze:
\"\"\"
{text}
\"\"\"

Extract every atomic factual claim. Output one claim per line in this exact format:
CLAIM_ID|SOURCE_SENTENCE|CLAIM_TEXT

Where:
- CLAIM_ID is a sequential number starting from 1
- SOURCE_SENTENCE is the sentence from the text that contains this claim
- CLAIM_TEXT is the atomic factual claim, stated clearly

Example output:
1|First, install it with pip install crewai.|The install command for CrewAI is "pip install crewai"
2|You'll need Python 3.10 or newer.|CrewAI requires Python 3.10 or newer
"""


def build_extract_prompt(text: str) -> tuple[str, str]:
    """Return (system_prompt, user_message) for claim extraction."""
    return _EXTRACT_SYSTEM, _EXTRACT_USER_TEMPLATE.format(text=text)


def parse_extracted_claims(raw_response: str) -> list[Claim]:
    """Parse the LLM response into a list of Claims."""
    claims: list[Claim] = []
    for line in raw_response.strip().splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        try:
            claim_id = int(parts[0].strip())
        except ValueError:
            continue
        claims.append(Claim(
            claim_id=claim_id,
            source_sentence=parts[1].strip(),
            text=parts[2].strip(),
        ))
    return claims


def extract_claims_interactive(text: str) -> list[Claim]:
    """Print the extraction prompt and read back the LLM response."""
    system, user = build_extract_prompt(text)
    separator = "=" * 70
    print(f"\n{separator}")
    print("CLAIM EXTRACTION")
    print("Paste the following into Claude Code, Codex CLI, or Gemini CLI:")
    print(f"{separator}")
    print(f"SYSTEM: {system}")
    print(f"\nUSER MESSAGE:\n{user}")
    print(f"{separator}")
    print("Paste the LLM response below, then enter END_OF_RESPONSE on a new line:")
    print(separator)

    lines: list[str] = []
    for line in sys.stdin:
        if line.strip() == "END_OF_RESPONSE":
            break
        lines.append(line)

    return parse_extracted_claims("".join(lines))


# ---------------------------------------------------------------------------
# Step 2: Claim verification
# ---------------------------------------------------------------------------

_VERIFY_SYSTEM = (
    "You are a fact-checking judge. Given a factual claim and reference "
    "documentation, determine if the claim is correct, incorrect, or "
    "unverifiable based solely on the provided documentation."
)

_VERIFY_USER_TEMPLATE = """Reference documentation:
\"\"\"
{reference_text}
\"\"\"

Claims to verify (one per line):
{claims_block}

For each claim, respond with exactly one line in this format:
CLAIM_ID|VERDICT|EVIDENCE

Where:
- CLAIM_ID matches the input claim ID
- VERDICT is exactly one of: CORRECT, INCORRECT, UNVERIFIABLE
- EVIDENCE is a brief explanation referencing the documentation

Rules:
- CORRECT: The documentation explicitly supports this claim
- INCORRECT: The documentation explicitly contradicts this claim
- UNVERIFIABLE: The documentation does not contain enough information to verify
"""


def build_verify_prompt(
    claims: list[Claim],
    reference_text: str,
) -> tuple[str, str]:
    """Return (system_prompt, user_message) for claim verification."""
    claims_block = "\n".join(
        f"{c.claim_id}|{c.text}" for c in claims
    )
    user = _VERIFY_USER_TEMPLATE.format(
        reference_text=reference_text,
        claims_block=claims_block,
    )
    return _VERIFY_SYSTEM, user


def parse_verification_response(
    raw_response: str,
    claims: list[Claim],
) -> list[ClaimVerdict]:
    """Parse the LLM verification response into ClaimVerdicts."""
    claim_map = {c.claim_id: c.text for c in claims}
    verdicts: list[ClaimVerdict] = []

    for line in raw_response.strip().splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|", 2)
        if len(parts) < 2:
            continue
        try:
            claim_id = int(parts[0].strip())
        except ValueError:
            continue

        verdict_str = parts[1].strip().upper()
        if verdict_str not in {"CORRECT", "INCORRECT", "UNVERIFIABLE"}:
            verdict_str = "UNVERIFIABLE"

        evidence = parts[2].strip() if len(parts) >= 3 else ""
        claim_text = claim_map.get(claim_id, "")

        verdicts.append(ClaimVerdict(
            claim_id=claim_id,
            claim_text=claim_text,
            verdict=verdict_str,
            evidence=evidence,
        ))

    return verdicts


def verify_claims_interactive(
    claims: list[Claim],
    reference_text: str,
) -> list[ClaimVerdict]:
    """Print the verification prompt and read back the LLM response."""
    system, user = build_verify_prompt(claims, reference_text)
    separator = "=" * 70
    print(f"\n{separator}")
    print("CLAIM VERIFICATION")
    print("Paste the following into Claude Code, Codex CLI, or Gemini CLI:")
    print(f"(Use a DIFFERENT model than the one that generated the text)")
    print(f"{separator}")
    print(f"SYSTEM: {system}")
    print(f"\nUSER MESSAGE:\n{user}")
    print(f"{separator}")
    print("Paste the LLM response below, then enter END_OF_RESPONSE on a new line:")
    print(separator)

    lines: list[str] = []
    for line in sys.stdin:
        if line.strip() == "END_OF_RESPONSE":
            break
        lines.append(line)

    return parse_verification_response("".join(lines), claims)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def compute_factual_precision(verdicts: list[ClaimVerdict]) -> float:
    """Compute factual precision: correct / (correct + incorrect).

    Returns 0.0 if no claims are verifiable (all UNVERIFIABLE or empty).
    """
    correct = sum(1 for v in verdicts if v.verdict == "CORRECT")
    incorrect = sum(1 for v in verdicts if v.verdict == "INCORRECT")
    total_verifiable = correct + incorrect
    if total_verifiable == 0:
        return 0.0
    return correct / total_verifiable


# ---------------------------------------------------------------------------
# Full scoring pipeline
# ---------------------------------------------------------------------------

def score_document(
    text: str,
    task_id: str,
    condition: str,
    run_id: str,
    reference_text: str,
    model: str = "",
    word_target: str = "",
) -> FactCheckResult:
    """Run the full claim-extraction + verification pipeline on one document.

    1. Extract claims from the generated text (interactive)
    2. Verify claims against reference documentation (interactive)
    3. Compute factual precision and return results
    """
    claims = extract_claims_interactive(text)

    if not claims:
        return FactCheckResult(
            task_id=task_id,
            condition=condition,
            run_id=run_id,
            model=model,
            word_target=word_target,
            claims=[],
            total_claims=0,
            correct_claims=0,
            incorrect_claims=0,
            unverifiable_claims=0,
            factual_precision=0.0,
        )

    verdicts = verify_claims_interactive(claims, reference_text)

    correct = sum(1 for v in verdicts if v.verdict == "CORRECT")
    incorrect = sum(1 for v in verdicts if v.verdict == "INCORRECT")
    unverifiable = sum(1 for v in verdicts if v.verdict == "UNVERIFIABLE")

    return FactCheckResult(
        task_id=task_id,
        condition=condition,
        run_id=run_id,
        model=model,
        word_target=word_target,
        claims=verdicts,
        total_claims=len(verdicts),
        correct_claims=correct,
        incorrect_claims=incorrect,
        unverifiable_claims=unverifiable,
        factual_precision=compute_factual_precision(verdicts),
    )


# ---------------------------------------------------------------------------
# File-based prompt workflow
# ---------------------------------------------------------------------------

LENGTH_LABELS = {"800-1000": "medium", "1500-2000": "long"}


def _factcheck_output_path(
    task_id: str,
    condition: str,
    run_id: str,
    model_key: str,
    word_target: str,
) -> Path:
    """Return the path where the CLI tool should save fact-check output."""
    length = LENGTH_LABELS.get(word_target, word_target)
    return FACTUAL_DIR / "outputs" / f"{task_id}_{condition}_{model_key}_{length}_{run_id}.txt"


def _build_factcheck_prompt(
    generated_text_path: Path,
    context_dir: Path,
    save_path: Path,
) -> str:
    """Build a combined extract+verify prompt for a single generated text."""
    return (
        "You are a fact-checking assistant. Your task is to extract factual claims "
        "from a blog post and verify each claim against reference documentation.\n\n"
        f"1. Read the blog post from {generated_text_path}\n"
        f"2. Read the reference documentation from {context_dir}\n\n"
        "## Step 1: Extract Claims\n"
        "Extract every atomic factual claim from the blog post. A factual claim is "
        "a statement that can be verified as true or false against documentation "
        "(version numbers, commands, file names, configuration details, behavioral "
        "descriptions, compatibility statements). Exclude opinions, subjective "
        "assessments, and hedged statements.\n\n"
        "## Step 2: Verify Claims\n"
        "For each extracted claim, check the reference documentation and determine "
        "if the claim is CORRECT, INCORRECT, or UNVERIFIABLE.\n"
        "- CORRECT: The documentation explicitly supports this claim\n"
        "- INCORRECT: The documentation explicitly contradicts this claim\n"
        "- UNVERIFIABLE: The documentation does not contain enough information\n\n"
        "## Output Format\n"
        "Output ONLY lines in this exact pipe-delimited format, one claim per line:\n\n"
        "CLAIM_ID|CLAIM_TEXT|VERDICT|EVIDENCE\n\n"
        "Where:\n"
        "- CLAIM_ID is a sequential number starting from 1\n"
        "- CLAIM_TEXT is the atomic factual claim\n"
        "- VERDICT is exactly one of: CORRECT, INCORRECT, UNVERIFIABLE\n"
        "- EVIDENCE is a brief explanation referencing the documentation\n\n"
        "Example output:\n"
        '1|The install command for CrewAI is "pip install crewai"|CORRECT|'
        "Documentation shows pip install crewai as the install command\n"
        "2|CrewAI requires Python 3.10 or newer|CORRECT|"
        "README states Python >=3.10 is required\n"
        "3|CrewAI supports GPT-5 out of the box|UNVERIFIABLE|"
        "No mention of GPT-5 support in the documentation\n\n"
        "Do not include any other text, headers, or commentary. "
        "Output ONLY the pipe-delimited lines.\n\n"
        f"Save the output to {save_path}\n"
        "Write only the pipe-delimited claim lines to the file, nothing else."
    )


def build_factcheck_prompts(
    tasks: list[Task],
    gen_texts: list[GeneratedText],
    model_key: str = "claude",
) -> list[dict]:
    """Build fact-check prompts for all generated texts and save to prompt files.

    Returns a list of prompt records. Also writes grouped prompt .txt files
    to data/generated/prompts/.
    """
    task_map = {t.task_id: t for t in tasks}
    records: list[dict] = []

    for gen in gen_texts:
        task = task_map.get(gen.task_id)
        if not task:
            continue

        context_dir = Path(task.context_dir)
        if not context_dir.is_absolute():
            context_dir = ROOT_DIR / context_dir

        wt = gen.word_target or "800-1000"
        length = LENGTH_LABELS.get(wt, wt)

        # Path to the generated text file on disk
        from ai_text_quality.generate import _output_file_path
        gen_path = _output_file_path(
            gen.condition, gen.task_id, gen.run_id, model_key, wt,
        )

        save_path = _factcheck_output_path(
            gen.task_id, gen.condition, gen.run_id, model_key, wt,
        )
        save_path.parent.mkdir(parents=True, exist_ok=True)

        prompt = _build_factcheck_prompt(gen_path, context_dir, save_path)

        records.append({
            "task_id": gen.task_id,
            "condition": gen.condition,
            "run_id": gen.run_id,
            "model_key": model_key,
            "word_target": wt,
            "prompt": prompt,
            "save_path": str(save_path),
        })

    files = write_grouped_prompts(records, prefix="factcheck")
    print(f"Built {len(records)} fact-check prompts -> {len(files)} files in data/generated/prompts/")
    for f in files:
        print(f"  {f.name}")
    return records


def parse_factcheck_output(raw_text: str) -> list[ClaimVerdict]:
    """Parse the combined extract+verify output into ClaimVerdicts."""
    verdicts: list[ClaimVerdict] = []
    for line in raw_text.strip().splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|", 3)
        if len(parts) < 3:
            continue
        try:
            claim_id = int(parts[0].strip())
        except ValueError:
            continue

        claim_text = parts[1].strip()
        verdict_str = parts[2].strip().upper()
        if verdict_str not in {"CORRECT", "INCORRECT", "UNVERIFIABLE"}:
            verdict_str = "UNVERIFIABLE"
        evidence = parts[3].strip() if len(parts) >= 4 else ""

        verdicts.append(ClaimVerdict(
            claim_id=claim_id,
            claim_text=claim_text,
            verdict=verdict_str,
            evidence=evidence,
        ))
    return verdicts


def load_factcheck_outputs(
    tasks: list[Task],
    gen_texts: list[GeneratedText],
    model_key: str = "claude",
) -> list[FactCheckResult]:
    """Load fact-check output files from disk and return FactCheckResult objects."""
    task_map = {t.task_id: t for t in tasks}
    results: list[FactCheckResult] = []
    missing = 0

    for gen in gen_texts:
        task = task_map.get(gen.task_id)
        if not task:
            continue

        wt = gen.word_target or "800-1000"
        output_path = _factcheck_output_path(
            gen.task_id, gen.condition, gen.run_id, model_key, wt,
        )

        if not output_path.exists():
            missing += 1
            continue

        raw = output_path.read_text(encoding="utf-8")
        verdicts = parse_factcheck_output(raw)

        correct = sum(1 for v in verdicts if v.verdict == "CORRECT")
        incorrect = sum(1 for v in verdicts if v.verdict == "INCORRECT")
        unverifiable = sum(1 for v in verdicts if v.verdict == "UNVERIFIABLE")

        results.append(FactCheckResult(
            task_id=gen.task_id,
            condition=gen.condition,
            run_id=gen.run_id,
            model=gen.model,
            word_target=wt,
            claims=verdicts,
            total_claims=len(verdicts),
            correct_claims=correct,
            incorrect_claims=incorrect,
            unverifiable_claims=unverifiable,
            factual_precision=compute_factual_precision(verdicts),
        ))

    if missing:
        print(f"Warning: {missing} fact-check output files not found")
    print(f"Loaded {len(results)} fact-check results from output files")
    return results
