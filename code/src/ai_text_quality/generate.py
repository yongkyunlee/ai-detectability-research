"""Text generation pipeline for AI detectability research.

Generates technical blog posts under three experimental conditions:
  C1 (context_rich)      - Code, docs, issues, and community context
  C2 (style_constrained) - Persona + anti-pattern rules with rich context
  C3 (humanized)         - LLM rewrite of C1 output to sound human

Supports multi-model generation (Claude Code, Codex CLI, Gemini CLI) and
content length variation (short/long).

Prompts are printed to the console so the user can paste them into the
appropriate CLI tool and paste back the response.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

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
    "short": "150-250",
    "long": "700-1000",
}
DEFAULT_WORD_TARGET = "short"

TEMPERATURE = 0.3
MAX_TOKENS = 2048


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


def _output_file_path(
    condition: str,
    task_id: str,
    run_id: str,
    model_key: str = DEFAULT_MODEL,
) -> Path:
    """Return the absolute path where the CLI tool should save the output."""
    return GENERATED_DIR / condition / f"{task_id}_{model_key}_{run_id}.md"


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
        The ``"humanized"`` condition is handled by
        :func:`generate_humanized` instead.
    style_rules:
        Required when *condition* is ``"style_constrained"``.  Expected keys:
        ``persona``, ``sentence_structure``, ``anti_patterns``,
        ``content_rules``.
    word_target:
        Word target range string (e.g. "150-250"). Required.
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
# Interactive prompt helpers
# ---------------------------------------------------------------------------

def _print_prompt_and_collect_response(
    prompt: str,
    model_key: str = DEFAULT_MODEL,
    save_path: Path | None = None,
) -> str:
    """Print a prompt for the user to paste into a CLI tool, then collect the response.

    If *save_path* is provided, the prompt already contains a save-to-file
    instruction.  The user presses Enter after the CLI tool finishes, and the
    response is read from the file.  Otherwise, falls back to the original
    stdin paste workflow.
    """
    display_name = MODEL_DISPLAY_NAMES.get(model_key, model_key)
    separator = "=" * 70
    print(f"\n{separator}")
    print(f"TARGET: {display_name}")
    print(f"{separator}")
    print("PROMPT:")
    print(f"{separator}")
    print(prompt)
    print(f"\n{separator}")

    if save_path is not None:
        # Ensure parent directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Output will be saved to: {save_path}")
        print("Press Enter after the CLI tool finishes writing the file...")
        input()
        if not save_path.exists():
            raise FileNotFoundError(
                f"Expected output file not found: {save_path}"
            )
        return save_path.read_text(encoding="utf-8").strip()

    # Fallback: manual paste
    print("Paste the LLM response below, then enter END_OF_RESPONSE on a new line:")
    print(separator)

    lines: list[str] = []
    for line in sys.stdin:
        if line.strip() == "END_OF_RESPONSE":
            break
        lines.append(line)

    return "".join(lines).strip()


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------

def _gather_all_context_texts(task: Task) -> list[str]:
    """Read all context files for overlap scoring."""
    return _read_context_dir(task.context_dir)


def generate_text(
    task: Task,
    condition: str,
    run_id: str,
    style_rules: dict | None = None,
    model_key: str = DEFAULT_MODEL,
    word_target: str | None = None,
) -> GeneratedText:
    """Generate text for a single task under a given condition.

    Prints the prompt for the user to paste into the target CLI tool,
    then reads back the response from the saved file.
    """
    effective_word_target = word_target or WORD_TARGETS[DEFAULT_WORD_TARGET]
    save_path = _output_file_path(condition, task.task_id, run_id, model_key)
    prompt = build_prompt(
        task, condition, style_rules, word_target=word_target, save_path=save_path,
    )

    display_name = MODEL_DISPLAY_NAMES.get(model_key, model_key)
    print(
        f"\n>>> Generating: task={task.task_id} condition={condition} "
        f"run={run_id} model={display_name} length={effective_word_target}"
    )
    generated = _print_prompt_and_collect_response(
        prompt, model_key=model_key, save_path=save_path,
    )

    context_texts = _gather_all_context_texts(task)
    overlap = compute_overlap(generated, context_texts)

    return GeneratedText(
        task_id=task.task_id,
        condition=condition,
        run_id=run_id,
        text=generated,
        model=MODELS.get(model_key, model_key),
        word_target=effective_word_target,
        timestamp=datetime.now(timezone.utc).isoformat(),
        token_usage={"input_tokens": 0, "output_tokens": 0},
        overlap_score=overlap,
    )


def generate_humanized(
    source_text: GeneratedText,
    run_id: str,
    model_key: str = DEFAULT_MODEL,
    word_target: str | None = None,
) -> GeneratedText:
    """C3: Rewrite *source_text* (typically C1 output) to sound human.

    Prints the rewrite prompt for the user to paste into the target CLI tool.
    """
    effective_word_target = word_target or source_text.word_target or WORD_TARGETS[DEFAULT_WORD_TARGET]
    save_path = _output_file_path(
        "humanized", source_text.task_id, run_id, model_key,
    )
    save_suffix = _save_instruction(save_path)
    prompt = (
        "You are an editor making AI-generated technical content sound natural.\n\n"
        "Rewrite this to sound like a human engineer wrote it. "
        "Preserve all technical facts. "
        "Do not add information not in the original.\n\n"
        f"{source_text.text}"
        f"{save_suffix}"
    )

    display_name = MODEL_DISPLAY_NAMES.get(model_key, model_key)
    print(
        f"\n>>> Humanizing: task={source_text.task_id} run={run_id} "
        f"model={display_name}"
    )
    generated = _print_prompt_and_collect_response(
        prompt, model_key=model_key, save_path=save_path,
    )

    return GeneratedText(
        task_id=source_text.task_id,
        condition="humanized",
        run_id=run_id,
        text=generated,
        model=MODELS.get(model_key, model_key),
        word_target=effective_word_target,
        timestamp=datetime.now(timezone.utc).isoformat(),
        token_usage={"input_tokens": 0, "output_tokens": 0},
        overlap_score=source_text.overlap_score,
    )


# ---------------------------------------------------------------------------
# Batch generation
# ---------------------------------------------------------------------------

def generate_all(
    tasks: list[Task],
    style_rules: dict,
    runs: int = 2,
    model_keys: list[str] | None = None,
    word_targets: list[str | None] | None = None,
) -> list[GeneratedText]:
    """Generate all conditions for all tasks across multiple runs, models, and lengths.

    Parameters
    ----------
    tasks:
        List of task definitions.
    style_rules:
        Style rules for C2 condition.
    runs:
        Number of runs per task-condition-model-length combination.
    model_keys:
        List of model keys to generate with. Defaults to [DEFAULT_MODEL].
    word_targets:
        List of word targets. None entries use the task default. Defaults to [None].

    Returns the full list of :class:`GeneratedText` objects.
    """
    if model_keys is None:
        model_keys = [DEFAULT_MODEL]
    if word_targets is None:
        word_targets = [None]

    results: list[GeneratedText] = []

    for model_key in model_keys:
        for wt in word_targets:
            for task in tasks:
                for run_idx in range(1, runs + 1):
                    run_id = f"run_{run_idx:02d}"
                    logger.info(
                        "Generating task=%s run=%s model=%s length=%s",
                        task.task_id, run_id, model_key, wt or WORD_TARGETS[DEFAULT_WORD_TARGET],
                    )

                    # C1: context_rich
                    c1: GeneratedText | None = None
                    try:
                        c1 = generate_text(
                            task, "context_rich", run_id,
                            model_key=model_key, word_target=wt,
                        )
                        results.append(c1)
                    except Exception:
                        logger.exception(
                            "Failed C1 for task=%s run=%s", task.task_id, run_id,
                        )

                    # C2: style_constrained
                    try:
                        c2 = generate_text(
                            task, "style_constrained", run_id,
                            style_rules=style_rules,
                            model_key=model_key, word_target=wt,
                        )
                        results.append(c2)
                    except Exception:
                        logger.exception(
                            "Failed C2 for task=%s run=%s", task.task_id, run_id,
                        )

                    # C3: humanized (rewrite of C1)
                    if c1 is not None:
                        try:
                            c3 = generate_humanized(
                                c1, run_id,
                                model_key=model_key, word_target=wt,
                            )
                            results.append(c3)
                        except Exception:
                            logger.exception(
                                "Failed C3 for task=%s run=%s",
                                task.task_id, run_id,
                            )

    logger.info("Generation complete: %d texts produced", len(results))
    return results
