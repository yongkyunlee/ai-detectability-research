from __future__ import annotations

from pathlib import Path

# ── Root ──────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # code/

# ── Top-level directories ────────────────────────────────────────────
CONFIGS_DIR = ROOT_DIR / "configs"
DATA_DIR = ROOT_DIR / "data"

# ── Data sub-trees ───────────────────────────────────────────────────
TASKS_DIR = DATA_DIR / "tasks"
CONTEXT_DIR = DATA_DIR / "context"
HUMAN_BASELINES_DIR = DATA_DIR / "human_baselines"
GENERATED_DIR = DATA_DIR / "generated"
PROMPTS_DIR = DATA_DIR / "generated" / "prompts"
RESULTS_DIR = DATA_DIR / "results"

# ── Results sub-directories ──────────────────────────────────────────
DETECTION_DIR = RESULTS_DIR / "detection"
FACTUAL_DIR = RESULTS_DIR / "factual"
LINGUISTIC_DIR = RESULTS_DIR / "linguistic"
SUMMARY_DIR = RESULTS_DIR / "summary"

# ── Condition directories ────────────────────────────────────────────
C1_DIR = GENERATED_DIR / "c1_context_rich"
C2_DIR = GENERATED_DIR / "c2_style_constrained"
C3_DIR = GENERATED_DIR / "c3_humanized"

# ── Condition label → directory mapping ──────────────────────────────
CONDITION_DIRS: dict[str, Path] = {
    "context_rich": C1_DIR,
    "style_constrained": C2_DIR,
    "humanized": C3_DIR,
}


# ── Helpers ──────────────────────────────────────────────────────────
def get_task_path(project: str, task_id: str) -> Path:
    return TASKS_DIR / project / f"{task_id}.yaml"


def get_context_path(project: str, category: str) -> Path:
    return CONTEXT_DIR / project / category


def get_output_path(condition: str, task_id: str, run_id: str) -> Path:
    return CONDITION_DIRS.get(condition, GENERATED_DIR / condition) / f"{task_id}_{run_id}.md"


def get_result_path(result_type: str, filename: str) -> Path:
    """Return a path inside the appropriate results sub-directory.

    result_type should be one of: detection, factual, linguistic, summary.
    """
    type_dirs: dict[str, Path] = {
        "detection": DETECTION_DIR,
        "factual": FACTUAL_DIR,
        "linguistic": LINGUISTIC_DIR,
        "summary": SUMMARY_DIR,
    }
    base = type_dirs.get(result_type, RESULTS_DIR / result_type)
    return base / filename


def ensure_dirs() -> None:
    """Create every directory in the project layout if it does not exist."""
    for d in (
        CONFIGS_DIR,
        CONFIGS_DIR / "projects",
        TASKS_DIR,
        CONTEXT_DIR,
        HUMAN_BASELINES_DIR,
        GENERATED_DIR,
        PROMPTS_DIR,
        C1_DIR,
        C2_DIR,
        C3_DIR,
        RESULTS_DIR,
        DETECTION_DIR,
        FACTUAL_DIR,
        LINGUISTIC_DIR,
        SUMMARY_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)
