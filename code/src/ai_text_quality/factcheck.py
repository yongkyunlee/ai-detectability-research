"""Factual accuracy checking against gold-standard slot values.

Supports literal, regex, and semantic (LLM-judge) matching strategies,
plus a hybrid pipeline that routes each fact to the appropriate checker.

For semantic checks, instead of calling the Anthropic API directly, the
prompt is printed so the user can paste it into Claude Code and paste
back the response.
"""

from __future__ import annotations

import re
import sys

from ai_text_quality.models import FactCheckResult, GoldFact, SlotVerdict


# ---------------------------------------------------------------------------
# Strict (deterministic) slot checks
# ---------------------------------------------------------------------------

def check_slot_literal(text: str, gold_fact: GoldFact) -> SlotVerdict:
    """Check if *gold_fact.value* appears literally in *text* (case-insensitive).

    Returns a CORRECT verdict with the matching snippet as evidence when found,
    or a MISSING verdict otherwise.
    """
    idx = text.lower().find(gold_fact.value.lower())
    if idx != -1:
        # Pull a window of context around the match for evidence
        start = max(0, idx - 30)
        end = min(len(text), idx + len(gold_fact.value) + 30)
        snippet = text[start:end]
        return SlotVerdict(
            field=gold_fact.field,
            expected=gold_fact.value,
            verdict="CORRECT",
            evidence=snippet,
        )
    return SlotVerdict(
        field=gold_fact.field,
        expected=gold_fact.value,
        verdict="MISSING",
        evidence="",
    )


def check_slot_regex(text: str, gold_fact: GoldFact) -> SlotVerdict:
    """Check if *gold_fact.value* (treated as a regex) matches anywhere in *text*.

    Returns CORRECT with the first match as evidence, or MISSING.
    """
    try:
        match = re.search(gold_fact.value, text, re.IGNORECASE)
    except re.error:
        # If the pattern is invalid fall back to a literal search
        return check_slot_literal(text, gold_fact)

    if match:
        return SlotVerdict(
            field=gold_fact.field,
            expected=gold_fact.value,
            verdict="CORRECT",
            evidence=match.group(),
        )
    return SlotVerdict(
        field=gold_fact.field,
        expected=gold_fact.value,
        verdict="MISSING",
        evidence="",
    )


def check_slot_strict(text: str, gold_fact: GoldFact) -> SlotVerdict:
    """Route to the appropriate deterministic checker based on *match_type*.

    Handles ``literal`` and ``regex`` types.  For ``semantic`` (which requires
    an LLM), returns MISSING so the caller knows no deterministic answer was
    available.
    """
    if gold_fact.match_type == "literal":
        return check_slot_literal(text, gold_fact)
    if gold_fact.match_type == "regex":
        return check_slot_regex(text, gold_fact)
    # semantic -- cannot handle without LLM
    return SlotVerdict(
        field=gold_fact.field,
        expected=gold_fact.value,
        verdict="MISSING",
        evidence="no deterministic check available for semantic match_type",
    )


# ---------------------------------------------------------------------------
# LLM-judge slot check (interactive)
# ---------------------------------------------------------------------------

_JUDGE_SYSTEM_PROMPT = (
    "You are a fact-checking judge. Given a text and an expected fact, "
    "determine if the text contains this fact."
)


def judge_slot_llm(text: str, gold_fact: GoldFact) -> SlotVerdict:
    """Use Claude as a judge for semantic fact-checking.

    Prints the prompt for the user to paste into Claude Code, then reads
    back the verdict response.
    """
    user_message = (
        f"Text:\n\"\"\"\n{text}\n\"\"\"\n\n"
        f"Expected fact field: {gold_fact.field}\n"
        f"Expected value: {gold_fact.value}\n\n"
        "Does the text contain this fact? Respond with exactly one of: "
        "CORRECT, INCORRECT, or MISSING, followed by a pipe character (|) "
        "and a brief explanation.\n"
        "Format: VERDICT|explanation"
    )

    separator = "=" * 70
    print(f"\n{separator}")
    print("LLM-JUDGE FACT CHECK")
    print(f"{separator}")
    print(f"SYSTEM PROMPT: {_JUDGE_SYSTEM_PROMPT}")
    print(f"\nUSER MESSAGE:")
    print(f"{separator}")
    print(user_message)
    print(f"{separator}")
    print("Paste the LLM response below (single line, e.g. CORRECT|The text mentions...):")
    print(separator)

    raw = ""
    for line in sys.stdin:
        raw = line.strip()
        if raw:
            break

    # Parse VERDICT|explanation
    verdict: str = "MISSING"
    evidence: str = raw

    if "|" in raw:
        parts = raw.split("|", 1)
        token = parts[0].strip().upper()
        if token in {"CORRECT", "INCORRECT", "MISSING"}:
            verdict = token
            evidence = parts[1].strip()
    else:
        # Fallback: check if the response starts with a known verdict
        upper = raw.upper()
        for v in ("CORRECT", "INCORRECT", "MISSING"):
            if upper.startswith(v):
                verdict = v
                evidence = raw[len(v):].strip().lstrip(":|-.").strip()
                break

    return SlotVerdict(
        field=gold_fact.field,
        expected=gold_fact.value,
        verdict=verdict,  # type: ignore[arg-type]
        evidence=evidence,
    )


# ---------------------------------------------------------------------------
# Hybrid (match-type-routed) pipeline
# ---------------------------------------------------------------------------

def check_slots_hybrid(text: str, gold_facts: list[GoldFact]) -> list[SlotVerdict]:
    """Check each gold fact using the strategy dictated by its *match_type*.

    - ``literal`` -> :func:`check_slot_literal`
    - ``regex``   -> :func:`check_slot_regex`
    - ``semantic``-> :func:`judge_slot_llm`
    """
    verdicts: list[SlotVerdict] = []
    for fact in gold_facts:
        if fact.match_type == "literal":
            verdicts.append(check_slot_literal(text, fact))
        elif fact.match_type == "regex":
            verdicts.append(check_slot_regex(text, fact))
        else:  # semantic
            verdicts.append(judge_slot_llm(text, fact))
    return verdicts


# ---------------------------------------------------------------------------
# Accuracy helpers
# ---------------------------------------------------------------------------

def compute_accuracy(verdicts: list[SlotVerdict]) -> float:
    """Fraction of verdicts that are CORRECT.

    Returns 0.0 when *verdicts* is empty.
    """
    if not verdicts:
        return 0.0
    correct = sum(1 for v in verdicts if v.verdict == "CORRECT")
    return correct / len(verdicts)


# ---------------------------------------------------------------------------
# Full scoring pipeline
# ---------------------------------------------------------------------------

def score_document(
    text: str,
    task_id: str,
    condition: str,
    run_id: str,
    gold_facts: list[GoldFact],
) -> FactCheckResult:
    """Run the complete fact-checking pipeline on one document.

    1. Hybrid checks (routes by *match_type*).
    2. Strict-only checks (literal + regex; semantic facts get MISSING).
    3. Computes both accuracy metrics.
    4. Returns a :class:`FactCheckResult`.
    """
    hybrid_verdicts = check_slots_hybrid(text, gold_facts)
    strict_verdicts = [check_slot_strict(text, fact) for fact in gold_facts]

    hybrid_acc = compute_accuracy(hybrid_verdicts)
    strict_acc = compute_accuracy(strict_verdicts)

    return FactCheckResult(
        task_id=task_id,
        condition=condition,
        run_id=run_id,
        slot_results=hybrid_verdicts,
        hybrid_slot_accuracy=hybrid_acc,
        strict_slot_accuracy=strict_acc,
    )


# ---------------------------------------------------------------------------
# LLM-judge agreement audit
# ---------------------------------------------------------------------------

def compute_llm_judge_agreement(
    text: str, gold_facts: list[GoldFact]
) -> float:
    """Run the LLM judge on *all* facts and compare with hybrid scoring.

    Returns the agreement rate (0--1) between the LLM-judge verdicts and the
    hybrid verdicts.  This serves as an audit / calibration metric.
    """
    if not gold_facts:
        return 0.0

    hybrid_verdicts = check_slots_hybrid(text, gold_facts)
    llm_verdicts = [judge_slot_llm(text, fact) for fact in gold_facts]

    agreements = sum(
        1
        for hv, lv in zip(hybrid_verdicts, llm_verdicts)
        if hv.verdict == lv.verdict
    )
    return agreements / len(gold_facts)
