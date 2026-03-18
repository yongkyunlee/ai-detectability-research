"""Tests for factual accuracy checking (no API calls for literal/regex)."""
import pytest
from ai_text_quality.models import GoldFact, SlotVerdict
from ai_text_quality.factcheck import check_slot_literal, check_slot_regex, check_slot_strict, compute_accuracy


def test_literal_match_found(sample_text):
    fact = GoldFact(field="install_cmd", value="pip install testlib", match_type="literal")
    result = check_slot_literal(sample_text, fact)
    assert result.verdict == "CORRECT"


def test_literal_match_not_found(sample_text):
    fact = GoldFact(field="install_cmd", value="npm install testlib", match_type="literal")
    result = check_slot_literal(sample_text, fact)
    assert result.verdict == "MISSING"


def test_literal_match_case_insensitive(sample_text):
    """Literal matching should be case-insensitive."""
    fact = GoldFact(field="install_cmd", value="PIP INSTALL TESTLIB", match_type="literal")
    result = check_slot_literal(sample_text, fact)
    assert result.verdict == "CORRECT"


def test_literal_match_provides_evidence(sample_text):
    """CORRECT verdicts should include evidence context."""
    fact = GoldFact(field="install_cmd", value="pip install testlib", match_type="literal")
    result = check_slot_literal(sample_text, fact)
    assert result.evidence  # non-empty
    assert "pip install testlib" in result.evidence.lower()


def test_regex_match_found(sample_text):
    fact = GoldFact(field="version", value=r"v\d+\.\d+\.\d+", match_type="regex")
    result = check_slot_regex(sample_text, fact)
    assert result.verdict == "CORRECT"
    assert "v2.3.1" in result.evidence


def test_regex_match_not_found(sample_text):
    fact = GoldFact(field="version", value=r"v\d+\.\d+\.\d+\.\d+", match_type="regex")
    result = check_slot_regex(sample_text, fact)
    assert result.verdict == "MISSING"


def test_regex_invalid_pattern_falls_back_to_literal(sample_text):
    """An invalid regex pattern should fall back to literal search."""
    fact = GoldFact(field="test", value="pip install testlib", match_type="regex")
    # This is actually a valid pattern (literal string), but let's test with a
    # truly invalid pattern that would also happen to match literally
    fact_invalid = GoldFact(field="test", value="[invalid regex", match_type="regex")
    result = check_slot_regex(sample_text, fact_invalid)
    # Should fall back to literal check and return MISSING (since "[invalid regex"
    # is not in the text)
    assert result.verdict == "MISSING"


def test_strict_routes_literal(sample_text):
    fact = GoldFact(field="install_cmd", value="pip install testlib", match_type="literal")
    result = check_slot_strict(sample_text, fact)
    assert result.verdict == "CORRECT"


def test_strict_routes_regex(sample_text):
    fact = GoldFact(field="version", value=r"v\d+\.\d+\.\d+", match_type="regex")
    result = check_slot_strict(sample_text, fact)
    assert result.verdict == "CORRECT"


def test_strict_skips_semantic(sample_text):
    fact = GoldFact(field="purpose", value="data processing", match_type="semantic")
    result = check_slot_strict(sample_text, fact)
    assert result.verdict == "MISSING"


def test_compute_accuracy():
    verdicts = [
        SlotVerdict(field="a", expected="x", verdict="CORRECT"),
        SlotVerdict(field="b", expected="y", verdict="CORRECT"),
        SlotVerdict(field="c", expected="z", verdict="MISSING"),
        SlotVerdict(field="d", expected="w", verdict="INCORRECT"),
    ]
    assert compute_accuracy(verdicts) == 0.5


def test_compute_accuracy_all_correct():
    verdicts = [
        SlotVerdict(field="a", expected="x", verdict="CORRECT"),
        SlotVerdict(field="b", expected="y", verdict="CORRECT"),
    ]
    assert compute_accuracy(verdicts) == 1.0


def test_compute_accuracy_none_correct():
    verdicts = [
        SlotVerdict(field="a", expected="x", verdict="MISSING"),
        SlotVerdict(field="b", expected="y", verdict="INCORRECT"),
    ]
    assert compute_accuracy(verdicts) == 0.0


def test_compute_accuracy_empty():
    assert compute_accuracy([]) == 0.0
