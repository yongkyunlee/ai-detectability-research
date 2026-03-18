"""Factual accuracy checking via claim extraction and verification.

Instead of matching against a pre-defined gold fact table, this module:
1. Extracts atomic factual claims from generated text (via LLM)
2. Verifies each claim against reference documentation (via LLM)
3. Computes factual precision = correct / (correct + incorrect)

All LLM interactions are interactive: prompts are printed for the user
to paste into a CLI tool (Claude Code, Codex CLI, or Gemini CLI).
"""

from __future__ import annotations

import sys

from ai_text_quality.models import Claim, ClaimVerdict, FactCheckResult


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
