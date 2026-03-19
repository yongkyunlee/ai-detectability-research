"""Linguistic feature extraction for AI-text quality analysis.

Extracts ten stylometric / structural features from a document that tend to
differentiate AI-generated text from human-written text.  All heavy NLP work
uses spaCy; statistical helpers use NumPy.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import numpy as np
import spacy
from spacy.tokens import Doc

from ai_text_quality.models import LinguisticFeatures

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# spaCy model loading
# ---------------------------------------------------------------------------

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None  # Handle gracefully if not installed

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DISCOURSE_MARKERS: list[str] = [
    "furthermore",
    "moreover",
    "additionally",
    "consequently",
    "it's worth noting",
    "it should be noted",
    "it's important to note",
    "in conclusion",
    "to summarize",
    "in summary",
    "in the world of",
    "in today's",
    "when it comes to",
    "let's dive in",
    "let's explore",
    "let's take a look",
    "arguably",
    "it could be said",
    "one might argue",
    "needless to say",
    "as a matter of fact",
    "it goes without saying",
    "at the end of the day",
]

CONTRACTION_PATTERNS: dict[str, str] = {
    r"\b(do not|don't)\b": "don't",
    r"\b(does not|doesn't)\b": "doesn't",
    r"\b(did not|didn't)\b": "didn't",
    r"\b(is not|isn't)\b": "isn't",
    r"\b(are not|aren't)\b": "aren't",
    r"\b(was not|wasn't)\b": "wasn't",
    r"\b(were not|weren't)\b": "weren't",
    r"\b(will not|won't)\b": "won't",
    r"\b(would not|wouldn't)\b": "wouldn't",
    r"\b(could not|couldn't)\b": "couldn't",
    r"\b(should not|shouldn't)\b": "shouldn't",
    r"\b(cannot|can't)\b": "can't",
    r"\b(it is|it's)\b": "it's",
    r"\b(I am|I'm)\b": "I'm",
    r"\b(we are|we're)\b": "we're",
    r"\b(they are|they're)\b": "they're",
    r"\b(I have|I've)\b": "I've",
    r"\b(we have|we've)\b": "we've",
    r"\b(you have|you've)\b": "you've",
    r"\b(I would|I'd)\b": "I'd",
    r"\b(we would|we'd)\b": "we'd",
}

FIRST_PERSON_WORDS: set[str] = {"i", "we", "my", "our", "me", "us"}


# ---------------------------------------------------------------------------
# Helper: paragraph splitting
# ---------------------------------------------------------------------------

def _split_paragraphs(text: str) -> list[str]:
    """Split text on blank lines, returning non-empty paragraphs."""
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]


# ---------------------------------------------------------------------------
# Feature functions
# ---------------------------------------------------------------------------

def compute_sentence_stats(doc: Doc) -> tuple[float, float]:
    """Mean and standard deviation of sentence lengths (in words).

    Returns ``(sent_len_mean, sent_len_std)``.  If the document has no
    sentences, returns ``(0.0, 0.0)``.
    """
    lengths = [len([t for t in sent if not t.is_space]) for sent in doc.sents]
    if not lengths:
        return 0.0, 0.0
    arr = np.array(lengths, dtype=float)
    return float(np.mean(arr)), float(np.std(arr))


def compute_vocab_diversity(text: str, max_words: int = 200) -> float:
    """Type-token ratio on the first *max_words* words.

    Returns ``unique_words / total_words``.  If the text has no words, returns
    0.0.
    """
    words = text.lower().split()[:max_words]
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def compute_contraction_rate(text: str) -> float:
    """Fraction of contraction opportunities where the contracted form is used.

    A *contraction opportunity* is any location where either the contracted or
    the expanded form appears.  The rate equals ``contracted / total``.
    Returns 0.0 when there are no opportunities.
    """
    contracted = 0
    total = 0
    for pattern in CONTRACTION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            total += 1
            # The matched group is one of the two alternatives.
            # If it contains an apostrophe it's a contraction.
            if "\u2019" in m or "'" in m:
                contracted += 1
    if total == 0:
        return 0.0
    return contracted / total


def compute_first_person_rate(text: str) -> float:
    """Count of first-person words divided by total words (lowercased)."""
    words = text.lower().split()
    if not words:
        return 0.0
    count = sum(1 for w in words if w.strip(".,!?;:\"'()[]") in FIRST_PERSON_WORDS)
    return count / len(words)


def compute_discourse_marker_rate(text: str, n_sentences: int) -> float:
    """Occurrences of discourse markers per sentence (case-insensitive).

    Returns 0.0 when *n_sentences* is zero.
    """
    if n_sentences == 0:
        return 0.0
    lower = text.lower()
    count = sum(lower.count(marker) for marker in DISCOURSE_MARKERS)
    return count / n_sentences


def compute_list_density(text: str) -> float:
    """List items per paragraph.

    A *list item* is a line beginning with ``-``, ``*``, or a number followed
    by a dot (e.g. ``1.``).  Paragraphs are separated by blank lines.
    Returns 0.0 if there are no paragraphs.
    """
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return 0.0
    list_pattern = re.compile(r"^\s*(?:[-*]|\d+\.)\s", re.MULTILINE)
    list_items = len(list_pattern.findall(text))
    return list_items / len(paragraphs)


def compute_passive_ratio(doc: Doc) -> float:
    """Fraction of sentences that contain passive voice.

    Detection heuristic: a sentence is passive if it contains a token whose
    dependency label is ``nsubjpass`` or ``auxpass``.
    """
    sents = list(doc.sents)
    if not sents:
        return 0.0
    passive_count = 0
    for sent in sents:
        for token in sent:
            if token.dep_ in {"nsubjpass", "auxpass"}:
                passive_count += 1
                break
    return passive_count / len(sents)


def compute_paragraph_len_std(text: str) -> float:
    """Standard deviation of word counts across paragraphs.

    Paragraphs are separated by blank lines.  Returns 0.0 when there are fewer
    than two paragraphs.
    """
    paragraphs = _split_paragraphs(text)
    if len(paragraphs) < 2:
        return 0.0
    lengths = np.array([len(p.split()) for p in paragraphs], dtype=float)
    return float(np.std(lengths))


def compute_specificity_score(doc: Doc) -> float:
    """(Named entities + numeric tokens) per sentence.

    Returns 0.0 when the document has no sentences.
    """
    sents = list(doc.sents)
    if not sents:
        return 0.0
    n_entities = len(doc.ents)
    n_numbers = sum(1 for token in doc if token.like_num)
    return (n_entities + n_numbers) / len(sents)


# ---------------------------------------------------------------------------
# Main feature extraction
# ---------------------------------------------------------------------------

def extract_features(
    text: str,
    task_id: str,
    condition: str,
    run_id: str,
    model: str = "",
    word_target: str = "",
) -> LinguisticFeatures:
    """Compute all ten linguistic features for a document.

    Processes *text* through spaCy once, then delegates to the individual
    ``compute_*`` functions.

    Raises :class:`RuntimeError` if the spaCy model is not available.
    """
    if nlp is None:
        raise RuntimeError(
            "spaCy model 'en_core_web_sm' is not installed. "
            "Run: python -m spacy download en_core_web_sm"
        )

    doc = nlp(text)
    sents = list(doc.sents)
    n_sentences = len(sents)

    sent_len_mean, sent_len_std = compute_sentence_stats(doc)

    return LinguisticFeatures(
        task_id=task_id,
        condition=condition,
        run_id=run_id,
        model=model,
        word_target=word_target,
        sent_len_mean=sent_len_mean,
        sent_len_std=sent_len_std,
        vocab_diversity=compute_vocab_diversity(text),
        contraction_rate=compute_contraction_rate(text),
        first_person_rate=compute_first_person_rate(text),
        discourse_marker_rate=compute_discourse_marker_rate(text, n_sentences),
        list_density=compute_list_density(text),
        passive_ratio=compute_passive_ratio(doc),
        paragraph_len_std=compute_paragraph_len_std(text),
        specificity_score=compute_specificity_score(doc),
    )


# ---------------------------------------------------------------------------
# Style distance
# ---------------------------------------------------------------------------

_FEATURE_FIELDS: list[str] = [
    "sent_len_std",
    "sent_len_mean",
    "vocab_diversity",
    "contraction_rate",
    "first_person_rate",
    "discourse_marker_rate",
    "list_density",
    "passive_ratio",
    "paragraph_len_std",
    "specificity_score",
]


def compute_style_distance(
    features: LinguisticFeatures,
    baseline_mean: dict[str, float],
) -> float:
    """Cosine distance between a feature vector and a baseline mean vector.

    Both vectors are L2-normalized before the cosine similarity is computed.
    The cosine *distance* is ``1 - cosine_similarity``.

    *baseline_mean* maps feature names (matching the ``LinguisticFeatures``
    field names) to their mean values from the reference condition (e.g. C5).

    Returns 0.0 if either vector has zero magnitude (degenerate case).
    """
    feat_vec = np.array(
        [getattr(features, f) for f in _FEATURE_FIELDS], dtype=float
    )
    base_vec = np.array(
        [baseline_mean.get(f, 0.0) for f in _FEATURE_FIELDS], dtype=float
    )

    norm_feat = np.linalg.norm(feat_vec)
    norm_base = np.linalg.norm(base_vec)

    if norm_feat == 0.0 or norm_base == 0.0:
        return 0.0

    cosine_sim = float(np.dot(feat_vec, base_vec) / (norm_feat * norm_base))
    # Clamp to [-1, 1] to guard against floating-point drift
    cosine_sim = max(-1.0, min(1.0, cosine_sim))
    return 1.0 - cosine_sim
