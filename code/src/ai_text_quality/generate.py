"""Text generation pipeline for AI detectability research.

Generates technical blog posts under three experimental conditions:
  C1 (context_rich)      - Code, docs, issues, and community context
  C2 (style_constrained) - Persona + anti-pattern rules with rich context
  C3 (humanized)         - LLM rewrite of C1 output to sound human

Workflow (non-interactive, notebook-friendly):
  1. build_all_prompts()  → writes prompts.jsonl (C1 + C2)
  2. User pastes each prompt into the appropriate CLI tool
  3. build_humanize_prompts() → appends C3 prompts (needs C1 outputs on disk)
  4. User pastes C3 prompts
  5. load_all_generated() → reads output files, computes overlap, returns GeneratedText list
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from ai_text_quality.io_utils import save_prompt, write_grouped_prompts
from ai_text_quality.models import GeneratedText, Task
from ai_text_quality.paths import GENERATED_DIR, ROOT_DIR

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model and length configuration
# ---------------------------------------------------------------------------

MODELS = {
    "claude": "claude-opus-4-6 (Claude Code)",
    "codex": "codex-cli (Codex CLI)",
    "gemini": "gemini-3.1 (Gemini CLI)",
}
DEFAULT_MODEL = "claude"

MODEL_DISPLAY_NAMES = {
    "claude": "Claude Code (Opus 4.6)",
    "codex": "Codex CLI (GPT 5.4)",
    "gemini": "Gemini CLI (Gemini 3.1)",
}

WORD_TARGETS = {
    "medium": "800-1000",
    "long": "1500-2000",
}
DEFAULT_WORD_TARGET = "medium"

TEMPERATURE = 0.3
MAX_TOKENS = 4096


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _resolve_context_dir(directory: str) -> Path:
    """Resolve a context_dir (possibly relative) against ROOT_DIR."""
    p = Path(directory)
    if not p.is_absolute():
        p = ROOT_DIR / p
    return p


def _read_context_dir(directory: str) -> list[str]:
    """Read all text files under *directory* recursively.

    Used for overlap scoring — not for prompt construction (prompts just
    reference the directory path so the CLI tool can read it directly).
    """
    contents: list[str] = []
    root = _resolve_context_dir(directory)
    if not root.is_dir():
        logger.warning("Context directory does not exist: %s", root)
        return contents
    for child in sorted(root.rglob("*")):
        if child.is_file():
            try:
                contents.append(child.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                pass
    return contents


LENGTH_LABELS = {"800-1000": "medium", "1500-2000": "long"}


def _output_file_path(
    condition: str,
    task_id: str,
    run_id: str,
    model_key: str = DEFAULT_MODEL,
    word_target: str | None = None,
) -> Path:
    """Return the absolute path where the CLI tool should save the output."""
    effective_wt = word_target or WORD_TARGETS[DEFAULT_WORD_TARGET]
    length = LENGTH_LABELS.get(effective_wt, effective_wt)
    return GENERATED_DIR / condition / f"{task_id}_{model_key}_{length}_{run_id}.md"


def _save_instruction(save_path: Path) -> str:
    """Return the save-to-file instruction appended to prompts."""
    return (
        f"\n\nSave the blog post to {save_path}\n"
        "Write only the blog post content to the file — no additional commentary, "
        "no markdown fences wrapping the whole file, and no meta-text."
    )


def build_prompt(
    task: Task,
    condition: str,
    style_rules: dict | None = None,
    word_target: str | None = None,
    save_path: Path | None = None,
) -> str:
    """Return a single prompt string for the given condition.

    Parameters
    ----------
    task:
        The task definition containing topic, context directory, etc.
    condition:
        One of ``"context_rich"`` or ``"style_constrained"``.
    style_rules:
        Required when *condition* is ``"style_constrained"``.
    word_target:
        Word target range string (e.g. "800-1000").
    save_path:
        If provided, appends an instruction for the CLI tool to save the output
        directly to this file path.
    """
    effective_word_target = word_target or WORD_TARGETS[DEFAULT_WORD_TARGET]
    context_dir = _resolve_context_dir(task.context_dir)
    word_instruction = f"Target length: approximately {effective_word_target} words."
    save_suffix = _save_instruction(save_path) if save_path else ""

    # -- C1: context_rich ----------------------------------------------------
    if condition == "context_rich":
        return (
            f"Write a technical blog post about {task.topic} "
            "based on the project documentation.\n\n"
            f"Read the source code, documentation, issues, and community "
            f"discussions in {context_dir} and write a blog post about "
            f"{task.topic}.\n\n"
            "Use the context for facts, terminology, and trade-offs only. "
            "Do not copy phrasing from context sources.\n\n"
            f"{word_instruction}"
            f"{save_suffix}"
        )

    # -- C2: style_constrained ----------------------------------------------
    if condition == "style_constrained":
        if not style_rules:
            raise ValueError(
                "style_rules must be provided for the style_constrained condition"
            )

        parts = [
            f"Write a technical blog post about {task.topic} "
            "based on the project documentation.",
            "",
        ]
        if "persona" in style_rules:
            parts.append(f"Persona: {style_rules['persona']}")
        if "sentence_structure" in style_rules:
            parts.append(
                f"Sentence structure rules: {style_rules['sentence_structure']}"
            )
        if "anti_patterns" in style_rules:
            anti = style_rules["anti_patterns"]
            if isinstance(anti, list):
                anti = "; ".join(anti)
            parts.append(f"Anti-patterns to avoid: {anti}")
        if "content_rules" in style_rules:
            parts.append(f"Content rules: {style_rules['content_rules']}")

        parts.append("")
        parts.append(
            f"Read the source code, documentation, issues, and community "
            f"discussions in {context_dir} and write a blog post about "
            f"{task.topic}.\n\n"
            "Use the context for facts, terminology, and trade-offs only. "
            "Do not copy phrasing from context sources.\n\n"
            f"{word_instruction}"
            f"{save_suffix}"
        )
        return "\n".join(parts)

    raise ValueError(f"Unknown condition: {condition!r}")


def _build_humanize_prompt(source_path: Path, save_path: Path) -> str:
    """Return a C3 humanization prompt that references the source file."""
    save_suffix = _save_instruction(save_path)
    return (
        "You are a senior engineer rewriting an AI-generated blog post so it reads "
        "like a human wrote it. Preserve every technical fact. Do not add information "
        "not in the original. Apply ALL of the following rules:\n\n"
        "## Banned words and phrases (never use these)\n"
        "- Transition words: Moreover, Furthermore, Additionally, In addition, "
        "Subsequently, Accordingly, Indeed, Notably, Importantly, Consequently\n"
        "- Filler openers: 'In today's world', 'In today's digital age', "
        "'In the realm of', 'When it comes to', 'It's important to note', "
        "'It's worth noting', 'Let's dive in', 'In conclusion', 'To summarize'\n"
        "- Overused adjectives: comprehensive, robust, seamless, cutting-edge, "
        "pivotal, crucial, vital, innovative, groundbreaking, transformative, "
        "holistic, nuanced, intricate, multifaceted, dynamic\n"
        "- Overused verbs: delve, embark, navigate, leverage, utilize, optimize, "
        "streamline, foster, cultivate, harness, unleash, unlock, elevate, "
        "empower, facilitate, underscore\n"
        "- Overused nouns/metaphors: tapestry, landscape, realm, journey, beacon, "
        "treasure trove, synergy, paradigm, cornerstone, catalyst, nexus\n"
        "- Intensifiers: meticulously, seamlessly, notably, remarkably, undeniably, "
        "fundamentally, inherently\n"
        "- Patterns: 'a myriad of', 'a plethora of', 'at its core', "
        "'not only... but also', 'serves as a testament to'\n\n"
        "## Sentence and paragraph structure\n"
        "- Vary sentence length aggressively: mix very short sentences (3-7 words) "
        "with long complex ones (25+ words) in the SAME paragraph. Do not keep "
        "sentences in a uniform 15-20 word range.\n"
        "- Use occasional sentence fragments for emphasis.\n"
        "- Vary paragraph length: use a mix of 1-sentence and 5-8 sentence paragraphs. "
        "Never write more than two paragraphs of similar length in a row.\n"
        "- Do NOT start consecutive sentences with the same word or part of speech.\n\n"
        "## Punctuation\n"
        "- NEVER use em dashes (\u2014 or --). Use commas, parentheses, colons, or "
        "rewrite the sentence instead.\n"
        "- Use semicolons occasionally.\n\n"
        "## Voice and tone\n"
        "- Use contractions naturally: don't, it's, we've, can't, wouldn't, I'm.\n"
        "- Use first person where appropriate ('I found', 'we ran into').\n"
        "- Include 1-2 mild opinions or subjective judgments "
        "('honestly this surprised me', 'the docs don't make this obvious').\n"
        "- Add occasional hedging that sounds genuinely uncertain "
        "('I think', 'from what I can tell', 'not 100% sure on this').\n"
        "- Use casual register shifts: an informal aside, a colloquial synonym "
        "('use' not 'utilize', 'help' not 'facilitate', 'fix' not 'remediate').\n\n"
        "## Anti-patterns\n"
        "- Do NOT use numbered or bulleted lists unless the content absolutely requires it. "
        "Convert lists to prose.\n"
        "- Do NOT use the '[Topic] is a [category] that [description]' formula.\n"
        "- Do NOT add trailing importance claims ('highlighting the significance of...', "
        "'reflecting the continued relevance of...').\n"
        "- Do NOT write a generic concluding paragraph that just restates the intro.\n"
        "- Do NOT repeat the same key term more than twice in 3 consecutive sentences. "
        "Use pronouns or colloquial synonyms instead.\n\n"
        f"Read the blog post from {source_path} and rewrite it following every rule above."
        f"{save_suffix}"
    )


# ---------------------------------------------------------------------------
# Overlap scoring
# ---------------------------------------------------------------------------

def compute_overlap(
    text: str,
    context_texts: list[str],
    n: int = 8,
) -> float:
    """Compute maximum n-gram overlap between *text* and any context source.

    Returns the fraction of n-grams in *text* that appear in at least one
    context source.  If *text* has fewer than *n* tokens the result is 0.0.
    """
    gen_tokens = text.lower().split()
    if len(gen_tokens) < n:
        return 0.0

    gen_ngrams = {
        tuple(gen_tokens[i : i + n]) for i in range(len(gen_tokens) - n + 1)
    }
    if not gen_ngrams:
        return 0.0

    context_ngrams: set[tuple[str, ...]] = set()
    for ctx in context_texts:
        tokens = ctx.lower().split()
        for i in range(len(tokens) - n + 1):
            context_ngrams.add(tuple(tokens[i : i + n]))

    overlap = gen_ngrams & context_ngrams
    return len(overlap) / len(gen_ngrams)


# ---------------------------------------------------------------------------
# Step 1: Build C1 + C2 prompts
# ---------------------------------------------------------------------------

def build_all_prompts(
    tasks: list[Task],
    style_rules: dict,
    runs: int = 2,
    model_keys: list[str] | None = None,
    word_targets: list[str | None] | None = None,
) -> list[dict]:
    """Build all C1/C2 prompts and save them to prompts.jsonl.

    Returns a list of prompt records (each dict has task_id, condition,
    run_id, model, word_target, prompt, save_path).
    """
    if model_keys is None:
        model_keys = [DEFAULT_MODEL]
    if word_targets is None:
        word_targets = [None]

    records: list[dict] = []

    for model_key in model_keys:
        for wt in word_targets:
            effective_wt = wt or WORD_TARGETS[DEFAULT_WORD_TARGET]
            for task in tasks:
                for run_idx in range(1, runs + 1):
                    run_id = f"run_{run_idx:02d}"

                    for condition in ("context_rich", "style_constrained"):
                        save_path = _output_file_path(
                            condition, task.task_id, run_id, model_key, wt,
                        )
                        save_path.parent.mkdir(parents=True, exist_ok=True)

                        prompt = build_prompt(
                            task,
                            condition,
                            style_rules=style_rules if condition == "style_constrained" else None,
                            word_target=wt,
                            save_path=save_path,
                        )

                        record = {
                            "task_id": task.task_id,
                            "condition": condition,
                            "run_id": run_id,
                            "model": MODELS.get(model_key, model_key),
                            "model_key": model_key,
                            "word_target": effective_wt,
                            "prompt": prompt,
                            "save_path": str(save_path),
                        }
                        records.append(record)
                        save_prompt(
                            task_id=task.task_id,
                            condition=condition,
                            run_id=run_id,
                            model=MODELS.get(model_key, model_key),
                            word_target=effective_wt,
                            prompt=prompt,
                        )

    files = write_grouped_prompts(records)
    print(f"Built {len(records)} C1/C2 prompts → {len(files)} files in data/generated/prompts/")
    for f in files:
        print(f"  {f.name}")
    return records


# ---------------------------------------------------------------------------
# Step 2: Build C3 (humanize) prompts — requires C1 outputs on disk
# ---------------------------------------------------------------------------

def build_humanize_prompts(
    tasks: list[Task],
    runs: int = 2,
    model_keys: list[str] | None = None,
    word_targets: list[str | None] | None = None,
) -> list[dict]:
    """Build C3 humanization prompts from C1 output files on disk.

    Call this after the user has generated all C1 outputs.
    Returns a list of prompt records and appends them to prompts.jsonl.
    """
    if model_keys is None:
        model_keys = [DEFAULT_MODEL]
    if word_targets is None:
        word_targets = [None]

    records: list[dict] = []
    missing: list[str] = []

    for model_key in model_keys:
        for wt in word_targets:
            effective_wt = wt or WORD_TARGETS[DEFAULT_WORD_TARGET]
            for task in tasks:
                for run_idx in range(1, runs + 1):
                    run_id = f"run_{run_idx:02d}"

                    c1_path = _output_file_path(
                        "context_rich", task.task_id, run_id, model_key, wt,
                    )
                    if not c1_path.exists():
                        missing.append(str(c1_path))
                        continue

                    save_path = _output_file_path(
                        "humanized", task.task_id, run_id, model_key, wt,
                    )
                    save_path.parent.mkdir(parents=True, exist_ok=True)

                    prompt = _build_humanize_prompt(c1_path, save_path)

                    record = {
                        "task_id": task.task_id,
                        "condition": "humanized",
                        "run_id": run_id,
                        "model": MODELS.get(model_key, model_key),
                        "model_key": model_key,
                        "word_target": effective_wt,
                        "prompt": prompt,
                        "save_path": str(save_path),
                    }
                    records.append(record)
                    save_prompt(
                        task_id=task.task_id,
                        condition="humanized",
                        run_id=run_id,
                        model=MODELS.get(model_key, model_key),
                        word_target=effective_wt,
                        prompt=prompt,
                    )

    if missing:
        print(f"Warning: {len(missing)} C1 output files not found, skipped C3 for those")
    files = write_grouped_prompts(records)
    print(f"Built {len(records)} C3 prompts → {len(files)} files in data/generated/prompts/")
    for f in files:
        print(f"  {f.name}")
    return records


# ---------------------------------------------------------------------------
# Step 3: Load generated outputs from disk
# ---------------------------------------------------------------------------

def load_all_generated(
    tasks: list[Task],
    runs: int = 2,
    model_keys: list[str] | None = None,
    word_targets: list[str | None] | None = None,
) -> list[GeneratedText]:
    """Read all generated output files from disk and return GeneratedText objects."""
    if model_keys is None:
        model_keys = [DEFAULT_MODEL]
    if word_targets is None:
        word_targets = [None]

    results: list[GeneratedText] = []
    missing: list[str] = []

    for model_key in model_keys:
        for wt in word_targets:
            effective_wt = wt or WORD_TARGETS[DEFAULT_WORD_TARGET]
            for task in tasks:
                for run_idx in range(1, runs + 1):
                    run_id = f"run_{run_idx:02d}"

                    for condition in ("context_rich", "style_constrained", "humanized"):
                        save_path = _output_file_path(
                            condition, task.task_id, run_id, model_key, wt,
                        )
                        if not save_path.exists():
                            missing.append(str(save_path))
                            continue

                        text = save_path.read_text(encoding="utf-8").strip()

                        results.append(GeneratedText(
                            task_id=task.task_id,
                            condition=condition,
                            run_id=run_id,
                            text=text,
                            model=MODELS.get(model_key, model_key),
                            word_target=effective_wt,
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            token_usage={"input_tokens": 0, "output_tokens": 0},
                        ))

    if missing:
        print(f"Warning: {len(missing)} output files not found")
    print(f"Loaded {len(results)} generated texts")
    return results
