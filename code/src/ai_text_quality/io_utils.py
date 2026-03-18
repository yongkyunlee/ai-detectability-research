from __future__ import annotations

import json
from pathlib import Path

import yaml

from ai_text_quality.models import GeneratedText
from ai_text_quality.paths import CONDITION_DIRS, GENERATED_DIR


# ── Markdown ─────────────────────────────────────────────────────────

def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_markdown(path: Path, content: str, metadata: dict | None = None) -> None:
    """Write a markdown file, optionally prepending YAML frontmatter."""
    path.parent.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []
    if metadata:
        parts.append("---")
        parts.append(yaml.dump(metadata, default_flow_style=False).rstrip())
        parts.append("---")
        parts.append("")
    parts.append(content)
    path.write_text("\n".join(parts), encoding="utf-8")


# ── JSONL ────────────────────────────────────────────────────────────

def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ── GeneratedText persistence ────────────────────────────────────────

def _condition_dir(condition: str) -> Path:
    return CONDITION_DIRS.get(condition, GENERATED_DIR / condition)


def _md_path(condition: str, task_id: str, run_id: str) -> Path:
    return _condition_dir(condition) / f"{task_id}_{run_id}.md"


def _sidecar_path(condition: str) -> Path:
    return _condition_dir(condition) / "metadata.jsonl"


def save_generated_text(gen: GeneratedText) -> None:
    """Persist a GeneratedText as a markdown file plus a JSONL sidecar entry.

    The markdown file contains the generated text (with frontmatter holding
    non-text fields).  The sidecar JSONL stores the full serialised record so
    metadata can be loaded back without parsing frontmatter.
    """
    md = _md_path(gen.condition, gen.task_id, gen.run_id)
    meta = gen.model_dump()
    text = meta.pop("text")
    write_markdown(md, text, metadata=meta)
    append_jsonl(_sidecar_path(gen.condition), gen.model_dump())


def load_generated_text(condition: str, task_id: str, run_id: str) -> GeneratedText:
    """Load a GeneratedText from its sidecar JSONL entry.

    Falls back to reading the markdown file directly if no matching sidecar
    record is found (returns a partially populated object in that case).
    """
    sidecar = _sidecar_path(condition)
    for record in read_jsonl(sidecar):
        if record.get("task_id") == task_id and record.get("run_id") == run_id:
            return GeneratedText(**record)

    # Fallback: read markdown and build a minimal GeneratedText
    md = _md_path(condition, task_id, run_id)
    text = read_markdown(md)

    # Strip YAML frontmatter if present
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
            body = parts[2].lstrip("\n")
            return GeneratedText(
                task_id=task_id,
                condition=condition,
                run_id=run_id,
                text=body,
                model=frontmatter.get("model", "unknown"),
                timestamp=frontmatter.get("timestamp", ""),
                token_usage=frontmatter.get("token_usage", {}),
                overlap_score=frontmatter.get("overlap_score", 0.0),
            )

    return GeneratedText(
        task_id=task_id,
        condition=condition,
        run_id=run_id,
        text=text,
        model="unknown",
        timestamp="",
        token_usage={},
    )
