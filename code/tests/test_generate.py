"""Tests for the generation module (no API calls)."""
from ai_text_quality.generate import build_prompt, compute_overlap


def test_build_prompt_c1(sample_task):
    """C1 should use minimal system prompt and code_only context."""
    system, user = build_prompt(sample_task, "code_only")
    assert "technical blog post" in system.lower()
    assert sample_task.topic in system
    # C1 should not include style rules
    assert "contraction" not in system.lower()


def test_build_prompt_c3_includes_style_rules(sample_task):
    """C3 should include style rules in the system prompt."""
    style_rules = {
        "persona": "You are a senior engineer.",
        "sentence_structure": ["Vary sentence length.", "Use contractions."],
        "anti_patterns": ["Never use 'Furthermore'."],
        "content_rules": ["Include specific details."],
    }
    system, user = build_prompt(sample_task, "style_constrained", style_rules=style_rules)
    assert "senior engineer" in system.lower()
    assert "contraction" in system.lower() or "Vary sentence" in system


def test_build_prompt_c2_uses_all_context(sample_task):
    """C2 should use both code_only and additional context sources."""
    system, user = build_prompt(sample_task, "context_rich")
    assert "technical blog post" in system.lower()
    assert "Do not copy phrasing" in user


def test_build_prompt_c3_raises_without_style_rules(sample_task):
    """C3 should raise ValueError if style_rules is not provided."""
    import pytest
    with pytest.raises(ValueError, match="style_rules must be provided"):
        build_prompt(sample_task, "style_constrained")


def test_build_prompt_unknown_condition_raises(sample_task):
    """Unknown condition should raise ValueError."""
    import pytest
    with pytest.raises(ValueError, match="Unknown condition"):
        build_prompt(sample_task, "nonexistent_condition")


def test_compute_overlap_no_match():
    text = "This is a completely unique sentence about something."
    contexts = ["Another different text about other topics entirely."]
    score = compute_overlap(text, contexts, n=4)
    assert score == 0.0


def test_compute_overlap_with_match():
    text = "The quick brown fox jumps over the lazy dog and runs away."
    contexts = ["The quick brown fox jumps over the lazy dog in the park."]
    score = compute_overlap(text, contexts, n=4)
    assert score > 0.0


def test_compute_overlap_identical():
    text = "one two three four five six seven eight nine ten"
    contexts = [text]
    score = compute_overlap(text, contexts, n=4)
    assert score == 1.0


def test_compute_overlap_short_text():
    """Text shorter than n tokens should return 0.0."""
    text = "too short"
    contexts = ["too short"]
    score = compute_overlap(text, contexts, n=4)
    assert score == 0.0
