from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Task(BaseModel):
    task_id: str
    project: str
    topic: str
    context_dir: str


class Claim(BaseModel):
    """An atomic factual claim extracted from generated text."""
    claim_id: int
    text: str
    source_sentence: str


class ClaimVerdict(BaseModel):
    """Verification result for a single claim."""
    claim_id: int
    claim_text: str
    verdict: Literal["CORRECT", "INCORRECT", "UNVERIFIABLE"]
    evidence: str = ""


class GeneratedText(BaseModel):
    task_id: str
    condition: str
    run_id: str
    text: str
    model: str
    word_target: str = ""
    timestamp: str
    token_usage: dict[str, int]  # input_tokens, output_tokens
    overlap_score: float = 0.0


class DetectionResult(BaseModel):
    task_id: str
    condition: str
    run_id: str
    model: str = ""
    word_target: str = ""
    gptzero_human_prob: float
    gptzero_mixed_prob: float = 0.0
    gptzero_generated_prob: float = 0.0
    gptzero_sentences: list[dict] = Field(default_factory=list)
    originality_ai_score: float = 0.0
    originality_human_score: float = 0.0
    originality_paragraphs: list[dict] = Field(default_factory=list)


class FactCheckResult(BaseModel):
    task_id: str
    condition: str
    run_id: str
    model: str = ""
    word_target: str = ""
    claims: list[ClaimVerdict]
    total_claims: int
    correct_claims: int
    incorrect_claims: int
    unverifiable_claims: int
    factual_precision: float  # correct / (correct + incorrect)


class LinguisticFeatures(BaseModel):
    task_id: str
    condition: str
    run_id: str
    model: str = ""
    word_target: str = ""
    sent_len_std: float
    sent_len_mean: float
    vocab_diversity: float
    contraction_rate: float
    first_person_rate: float
    discourse_marker_rate: float
    list_density: float
    passive_ratio: float
    paragraph_len_std: float
    specificity_score: float
