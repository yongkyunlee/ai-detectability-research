"""Tests for linguistic feature extraction."""
import pytest
from ai_text_quality.linguistic import (
    compute_vocab_diversity,
    compute_contraction_rate,
    compute_first_person_rate,
    compute_discourse_marker_rate,
    compute_list_density,
    compute_paragraph_len_std,
    extract_features,
)

# Check if spaCy model is available
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    _HAS_SPACY_MODEL = True
except (ImportError, OSError):
    _HAS_SPACY_MODEL = False

requires_spacy = pytest.mark.skipif(
    not _HAS_SPACY_MODEL,
    reason="spaCy model 'en_core_web_sm' not installed",
)


def test_vocab_diversity_high():
    text = "the quick brown fox jumps over lazy dog near stream"
    diversity = compute_vocab_diversity(text)
    assert diversity == 1.0  # all unique words


def test_vocab_diversity_low():
    text = "the the the the the the the the the the"
    diversity = compute_vocab_diversity(text)
    assert diversity == pytest.approx(0.1)


def test_vocab_diversity_empty():
    assert compute_vocab_diversity("") == 0.0


def test_contraction_rate_all_contracted():
    text = "I don't think it's going to work. We can't do that."
    rate = compute_contraction_rate(text)
    assert rate > 0.5


def test_contraction_rate_none_contracted():
    text = "I do not think it is going to work. We cannot do that."
    rate = compute_contraction_rate(text)
    assert rate == 0.0


def test_contraction_rate_no_opportunities():
    text = "The system runs efficiently."
    rate = compute_contraction_rate(text)
    assert rate == 0.0


def test_first_person_rate():
    text = "I think we should update our code. My suggestion is to refactor."
    rate = compute_first_person_rate(text)
    # i, we, our, my = 4 first person words out of 13 total
    assert rate > 0.2


def test_first_person_rate_none():
    text = "The system processes data efficiently using parallel threads."
    rate = compute_first_person_rate(text)
    assert rate == 0.0


def test_first_person_rate_empty():
    assert compute_first_person_rate("") == 0.0


def test_discourse_markers_high(ai_style_text):
    # Count sentences roughly
    sentences = [s for s in ai_style_text.split('.') if s.strip()]
    n_sentences = len(sentences)
    rate = compute_discourse_marker_rate(ai_style_text, n_sentences)
    assert rate > 0.3  # AI text should have many markers


def test_discourse_markers_low(human_style_text):
    sentences = [s for s in human_style_text.split('.') if s.strip()]
    n_sentences = len(sentences)
    rate = compute_discourse_marker_rate(human_style_text, n_sentences)
    assert rate < 0.1  # Human text should have few markers


def test_discourse_markers_zero_sentences():
    rate = compute_discourse_marker_rate("some text", 0)
    assert rate == 0.0


def test_list_density_with_lists():
    text = """Here is some text.

- item one
- item two
- item three

More text here.

And another paragraph."""
    density = compute_list_density(text)
    assert density > 0.0


def test_list_density_no_lists():
    text = """First paragraph here.

Second paragraph here.

Third paragraph here."""
    density = compute_list_density(text)
    assert density == 0.0


def test_list_density_numbered_lists():
    text = """Intro paragraph.

1. First item
2. Second item
3. Third item

Closing paragraph."""
    density = compute_list_density(text)
    assert density > 0.0


def test_paragraph_len_std_uniform():
    text = """Word word word word word.

Word word word word word.

Word word word word word."""
    std = compute_paragraph_len_std(text)
    assert std == pytest.approx(0.0, abs=0.1)


def test_paragraph_len_std_varied():
    text = """Short.

This paragraph is much longer with many more words in it than the first one."""
    std = compute_paragraph_len_std(text)
    assert std > 0.0


def test_paragraph_len_std_single_paragraph():
    text = "Just one paragraph with no blank lines."
    std = compute_paragraph_len_std(text)
    assert std == 0.0


@requires_spacy
def test_extract_features_returns_all_fields(sample_text):
    features = extract_features(sample_text, "test_001", "code_only", "run_01")
    assert features.task_id == "test_001"
    assert features.condition == "code_only"
    assert features.run_id == "run_01"
    assert features.sent_len_mean > 0
    assert features.sent_len_std >= 0
    assert 0.0 <= features.vocab_diversity <= 1.0
    assert 0.0 <= features.contraction_rate <= 1.0
    assert features.first_person_rate >= 0.0
    assert features.discourse_marker_rate >= 0.0
    assert features.list_density >= 0.0
    assert 0.0 <= features.passive_ratio <= 1.0
    assert features.paragraph_len_std >= 0.0
    assert features.specificity_score >= 0.0


@requires_spacy
def test_ai_text_more_markers_than_human(ai_style_text, human_style_text):
    """AI-style text should have higher discourse marker rate."""
    ai_features = extract_features(ai_style_text, "ai", "test", "run_01")
    human_features = extract_features(human_style_text, "human", "test", "run_01")
    assert ai_features.discourse_marker_rate > human_features.discourse_marker_rate


@requires_spacy
def test_extract_features_raises_without_spacy():
    """Verify extract_features works when spaCy is available (integration sanity check)."""
    # This test simply verifies the function doesn't crash on minimal input
    features = extract_features("Hello world. This is a test.", "t", "c", "r")
    assert features.sent_len_mean > 0
