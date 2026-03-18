from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GoldFact(BaseModel):
    field: str
    value: str
    match_type: Literal["literal", "regex", "semantic"] = "literal"


class ContextSources(BaseModel):
    code_only: list[str]
    additional: list[str] = Field(default_factory=list)


class Task(BaseModel):
    task_id: str
    project: str
    topic: str
    word_target: str
    gold_facts: list[GoldFact]
    context_sources: ContextSources


class GeneratedText(BaseModel):
    task_id: str
    condition: str
    run_id: str
    text: str
    model: str
    timestamp: str
    token_usage: dict[str, int]  # input_tokens, output_tokens
    overlap_score: float = 0.0


class SlotVerdict(BaseModel):
    field: str
    expected: str
    verdict: Literal["CORRECT", "INCORRECT", "MISSING"]
    evidence: str = ""


class DetectionResult(BaseModel):
    task_id: str
    condition: str
    run_id: str
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
    slot_results: list[SlotVerdict]
    hybrid_slot_accuracy: float
    strict_slot_accuracy: float
    llm_judge_agreement: float = 0.0


class LinguisticFeatures(BaseModel):
    task_id: str
    condition: str
    run_id: str
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
