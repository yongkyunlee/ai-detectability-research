"""Tests for detection module (no API calls - just parsing)."""
import pytest
from ai_text_quality.detect import parse_gptzero_result, parse_originality_result
from ai_text_quality.models import DetectionResult


def test_parse_gptzero_result():
    response = {
        "documents": [{
            "completely_generated_prob": 0.85,
            "mixed_prob": 0.10,
            "sentences": [
                {"sentence": "Test sentence.", "generated_prob": 0.9, "perplexity": 12.5}
            ]
        }]
    }
    result = parse_gptzero_result(response, "task_001", "code_only", "run_01")
    assert result.gptzero_generated_prob == pytest.approx(0.85)
    # human_prob = 1.0 - generated_prob - mixed_prob = 0.05
    assert result.gptzero_human_prob == pytest.approx(0.05)
    assert result.gptzero_mixed_prob == pytest.approx(0.10)
    assert result.task_id == "task_001"
    assert result.condition == "code_only"
    assert result.run_id == "run_01"
    assert len(result.gptzero_sentences) == 1


def test_parse_gptzero_result_empty_documents():
    """Handle response with empty documents list."""
    response = {"documents": []}
    result = parse_gptzero_result(response, "task_001", "code_only", "run_01")
    assert result.gptzero_generated_prob == 0.0
    assert result.gptzero_human_prob == pytest.approx(1.0)


def test_parse_gptzero_result_missing_documents_key():
    """Handle response with no documents key at all."""
    response = {}
    result = parse_gptzero_result(response, "task_001", "code_only", "run_01")
    assert result.gptzero_generated_prob == 0.0


def test_parse_originality_result():
    detection = DetectionResult(
        task_id="task_001", condition="code_only", run_id="run_01",
        gptzero_human_prob=0.05,
    )
    response = {
        "score": {"ai": 0.92, "original": 0.08}
    }
    result = parse_originality_result(response, detection)
    assert result.originality_ai_score == pytest.approx(0.92)
    assert result.originality_human_score == pytest.approx(0.08)
    # Original fields should be preserved
    assert result.task_id == "task_001"
    assert result.gptzero_human_prob == pytest.approx(0.05)


def test_parse_originality_result_with_paragraphs():
    """Originality.ai response may include per-paragraph breakdowns."""
    detection = DetectionResult(
        task_id="task_001", condition="code_only", run_id="run_01",
        gptzero_human_prob=0.0,
    )
    response = {
        "score": {"ai": 0.75, "original": 0.25},
        "paragraphs": [
            {"text": "First paragraph.", "score": {"ai": 0.80, "original": 0.20}},
            {"text": "Second paragraph.", "score": {"ai": 0.70, "original": 0.30}},
        ]
    }
    result = parse_originality_result(response, detection)
    assert result.originality_ai_score == pytest.approx(0.75)
    assert len(result.originality_paragraphs) == 2
    assert result.originality_paragraphs[0]["ai_score"] == pytest.approx(0.80)


def test_parse_originality_result_empty_score():
    """Handle response with missing score key."""
    detection = DetectionResult(
        task_id="task_001", condition="code_only", run_id="run_01",
        gptzero_human_prob=0.0,
    )
    response = {}
    result = parse_originality_result(response, detection)
    assert result.originality_ai_score == 0.0
    assert result.originality_human_score == 0.0
