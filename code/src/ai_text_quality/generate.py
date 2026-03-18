"""Text generation pipeline for AI detectability research.

Generates technical blog posts under four experimental conditions:
  C1 (code_only)        - Minimal prompt with code/docs context only
  C2 (context_rich)     - Minimal prompt with enriched context
  C3 (style_constrained)- Persona + anti-pattern rules with rich context
  C4 (humanized)        - LLM rewrite of C2 output to sound human

Supports multi-model generation (Claude Code, Codex CLI, Gemini CLI) and
content length variation (short/medium/long).

Prompts are printed to the console so the user can paste them into the
appropriate CLI tool and paste back the response.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from ai_text_quality.models import GeneratedText, Task

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
    "medium": "300-500",
    "long": "700-1000",
}
DEFAULT_WORD_TARGET = "medium"

TEMPERATURE = 0.3
MAX_TOKENS = 2048


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _read_context_files(paths: Sequence[str]) -> list[str]:
    """Read text content from a list of file paths.

    Skips files that cannot be read and logs a warning.
    """
    contents: list[str] = []
    for p in paths:
        try:
            contents.append(Path(p).read_text(encoding="utf-8"))
        except OSError:
            logger.warning("Could not read context file: %s", p)
    return contents


def build_prompt(
    task: Task,
    condition: str,
    style_rules: dict | None = None,
    word_target: str | None = None,
) -> tuple[str, str]:
    """Return ``(system_prompt, user_message)`` for the given condition.

    Parameters
    ----------
    task:
        The task definition containing topic, context sources, etc.
    condition:
        One of ``"code_only"``, ``"context_rich"``, or ``"style_constrained"``.
        The ``"humanized"`` condition is handled by
        :func:`generate_humanized` instead.
    style_rules:
        Required when *condition* is ``"style_constrained"``.  Expected keys:
        ``persona``, ``sentence_structure``, ``anti_patterns``,
        ``content_rules``.
    word_target:
        Override the task's default word target. If None, uses task.word_target.

    Returns
    -------
    tuple[str, str]
        ``(system_prompt, user_message)``
    """
    effective_word_target = word_target or task.word_target
    base_system = (
        f"Write a technical blog post about {task.topic} "
        "based on the following documentation."
    )
    word_instruction = f"\n\nTarget length: approximately {effective_word_target} words."

    # -- C1: code_only -------------------------------------------------------
    if condition == "code_only":
        code_texts = _read_context_files(task.context_sources.code_only)
        user_message = "\n\n---\n\n".join(code_texts) + word_instruction
        return base_system, user_message

    # -- C2: context_rich ----------------------------------------------------
    if condition == "context_rich":
        code_texts = _read_context_files(task.context_sources.code_only)
        additional_texts = _read_context_files(task.context_sources.additional)
        all_context = code_texts + additional_texts
        user_message = "\n\n---\n\n".join(all_context)
        user_message += (
            "\n\nUse the following context for facts, terminology, and "
            "trade-offs only. Do not copy phrasing from context sources."
        )
        user_message += word_instruction
        return base_system, user_message

    # -- C3: style_constrained ----------------------------------------------
    if condition == "style_constrained":
        if not style_rules:
            raise ValueError(
                "style_rules must be provided for the style_constrained condition"
            )

        system_parts = [base_system, ""]
        if "persona" in style_rules:
            system_parts.append(f"Persona: {style_rules['persona']}")
        if "sentence_structure" in style_rules:
            system_parts.append(
                f"Sentence structure rules: {style_rules['sentence_structure']}"
            )
        if "anti_patterns" in style_rules:
            anti = style_rules["anti_patterns"]
            if isinstance(anti, list):
                anti = "; ".join(anti)
            system_parts.append(f"Anti-patterns to avoid: {anti}")
        if "content_rules" in style_rules:
            system_parts.append(f"Content rules: {style_rules['content_rules']}")

        system_prompt = "\n".join(system_parts)

        code_texts = _read_context_files(task.context_sources.code_only)
        additional_texts = _read_context_files(task.context_sources.additional)
        all_context = code_texts + additional_texts
        user_message = "\n\n---\n\n".join(all_context)
        user_message += (
            "\n\nUse the following context for facts, terminology, and "
            "trade-offs only. Do not copy phrasing from context sources."
        )
        user_message += word_instruction
        return system_prompt, user_message

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
    system_prompt: str,
    user_message: str,
    model_key: str = DEFAULT_MODEL,
) -> str:
    """Print a prompt for the user to paste into a CLI tool, then read back the response."""
    display_name = MODEL_DISPLAY_NAMES.get(model_key, model_key)
    separator = "=" * 70
    print(f"\n{separator}")
    print(f"TARGET: {display_name}")
    print(f"{separator}")
    print("SYSTEM PROMPT:")
    print(f"{separator}")
    print(system_prompt)
    print(f"\n{separator}")
    print("USER MESSAGE:")
    print(f"{separator}")
    print(user_message)
    print(f"\n{separator}")
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
    """Read all context files (code_only + additional) for overlap scoring."""
    return (
        _read_context_files(task.context_sources.code_only)
        + _read_context_files(task.context_sources.additional)
    )


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
    then reads back the pasted response.
    """
    effective_word_target = word_target or task.word_target
    system_prompt, user_message = build_prompt(
        task, condition, style_rules, word_target=word_target,
    )

    display_name = MODEL_DISPLAY_NAMES.get(model_key, model_key)
    print(
        f"\n>>> Generating: task={task.task_id} condition={condition} "
        f"run={run_id} model={display_name} length={effective_word_target}"
    )
    generated = _print_prompt_and_collect_response(
        system_prompt, user_message, model_key=model_key,
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
    """C4: Rewrite *source_text* (typically C2 output) to sound human.

    Prints the rewrite prompt for the user to paste into the target CLI tool.
    """
    effective_word_target = word_target or source_text.word_target
    system_prompt = (
        "You are an editor making AI-generated technical content sound natural."
    )
    user_message = (
        "Rewrite this to sound like a human engineer wrote it. "
        "Preserve all technical facts. "
        "Do not add information not in the original.\n\n"
        f"{source_text.text}"
    )

    display_name = MODEL_DISPLAY_NAMES.get(model_key, model_key)
    print(
        f"\n>>> Humanizing: task={source_text.task_id} run={run_id} "
        f"model={display_name}"
    )
    generated = _print_prompt_and_collect_response(
        system_prompt, user_message, model_key=model_key,
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
    runs: int = 3,
    model_keys: list[str] | None = None,
    word_targets: list[str | None] | None = None,
) -> list[GeneratedText]:
    """Generate all conditions for all tasks across multiple runs, models, and lengths.

    Parameters
    ----------
    tasks:
        List of task definitions.
    style_rules:
        Style rules for C3 condition.
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
                        task.task_id, run_id, model_key, wt or task.word_target,
                    )

                    try:
                        c1 = generate_text(
                            task, "code_only", run_id,
                            model_key=model_key, word_target=wt,
                        )
                        results.append(c1)
                    except Exception:
                        logger.exception(
                            "Failed C1 for task=%s run=%s", task.task_id, run_id,
                        )

                    c2: GeneratedText | None = None
                    try:
                        c2 = generate_text(
                            task, "context_rich", run_id,
                            model_key=model_key, word_target=wt,
                        )
                        results.append(c2)
                    except Exception:
                        logger.exception(
                            "Failed C2 for task=%s run=%s", task.task_id, run_id,
                        )

                    try:
                        c3 = generate_text(
                            task, "style_constrained", run_id,
                            style_rules=style_rules,
                            model_key=model_key, word_target=wt,
                        )
                        results.append(c3)
                    except Exception:
                        logger.exception(
                            "Failed C3 for task=%s run=%s", task.task_id, run_id,
                        )

                    if c2 is not None:
                        try:
                            c4 = generate_humanized(
                                c2, run_id,
                                model_key=model_key, word_target=wt,
                            )
                            results.append(c4)
                        except Exception:
                            logger.exception(
                                "Failed C4 for task=%s run=%s",
                                task.task_id, run_id,
                            )

    logger.info("Generation complete: %d texts produced", len(results))
    return results
