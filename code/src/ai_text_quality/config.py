from __future__ import annotations

from pathlib import Path

import yaml

from ai_text_quality.models import Task
from ai_text_quality.paths import CONFIGS_DIR, TASKS_DIR


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_conditions() -> dict:
    return load_yaml(CONFIGS_DIR / "conditions.yaml")


def load_style_rules() -> dict:
    return load_yaml(CONFIGS_DIR / "style_rules.yaml")


def load_validators_config() -> dict:
    return load_yaml(CONFIGS_DIR / "validators.yaml")


def load_project_config(project: str) -> dict:
    return load_yaml(CONFIGS_DIR / "projects" / f"{project}.yaml")


def load_task(project: str, task_id: str) -> Task:
    data = load_yaml(TASKS_DIR / project / f"{task_id}.yaml")
    return Task(**data)


def load_all_tasks() -> list[Task]:
    """Walk every project directory under TASKS_DIR and load all task YAML files."""
    tasks: list[Task] = []
    if not TASKS_DIR.exists():
        return tasks
    for project_dir in sorted(TASKS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue
        for task_file in sorted(project_dir.glob("*.yaml")):
            data = load_yaml(task_file)
            tasks.append(Task(**data))
    return tasks
