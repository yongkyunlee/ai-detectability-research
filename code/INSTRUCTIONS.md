# Instructions: Running the AI Detectability Experiment

Step-by-step guide to reproduce the full experiment, from environment setup through final analysis.

---

## Prerequisites

- Python 3.10+
- Access to:
  - **Claude Code** (or another LLM chat interface) for text generation and LLM-judge fact checking
  - **GPTZero** web UI (https://gptzero.me) for AI detection
  - **Originality.ai** web UI (https://originality.ai) for AI detection

No API keys are required. All LLM and detection interactions happen via copy-paste through their respective UIs.

---

## Step 0: Environment Setup

```bash
cd code/

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install the package in editable mode
pip install -e .

# Download the spaCy model for linguistic analysis
python -m spacy download en_core_web_sm
```

Verify the installation:

```bash
python -c "from ai_text_quality import Task, GeneratedText; print('OK')"
python -m pytest tests/ -v
```

All 50 tests should pass.

---

## Step 1: Prepare Context Data

Before generating any text, you need to populate the context files referenced by the task definitions. Each task YAML in `data/tasks/` specifies which files it expects under `context_sources`.

For example, `data/tasks/crewai/task_001.yaml` expects:

```
context_sources:
  code_only:
    - data/context/crewai/code/installation.md
  additional:
    - data/context/crewai/issues/setup_issues.md
    - data/context/crewai/community/reddit_getting_started.md
```

**What to put in each directory:**

| Directory | Content | How to collect |
|---|---|---|
| `data/context/{project}/code/` | README, doc pages, source file excerpts | Copy from official project docs or repo |
| `data/context/{project}/issues/` | GitHub issue excerpts (title + body + top comments) | Search GitHub issues for topic-related threads |
| `data/context/{project}/community/` | Reddit/HN thread excerpts | Search Reddit/HN for topic discussions |
| `data/context/{project}/releases/` | Relevant changelog entries | Copy from project release notes |
| `data/context/{project}/competitor/` | Competitor docs covering the same concept | Short snippets from similar projects |

**Preprocessing rules (per PLAN.md Section 3.3):**
- Strip bullet formatting, marketing copy, and canned opening/closing phrases
- Keep factual content: version numbers, commands, config details, error messages, trade-offs
- Context is used for factual grounding only, not for borrowing phrasing

Save each file as plain markdown. The generator reads these files by path and includes them in the LLM prompt.

---

## Step 2: Collect Human Baselines (C5)

For each of the 15 task topics, find a real engineer-written blog post or documentation section covering the same subject.

**Selection criteria:**
- Written by a named human author
- Published on a credible platform (official blog, Dev.to, Medium, engineering blog)
- Covers the same technical scope as the task
- Trimmed to 300-500 words if longer

Save each baseline as a markdown file in `data/human_baselines/{project}/`:

```
data/human_baselines/crewai/baseline_001.md
data/human_baselines/crewai/baseline_002.md
...
data/human_baselines/duckdb/baseline_001.md
...
```

Record source URL and author in the file's YAML frontmatter:

```markdown
---
source_url: https://example.com/blog/crewai-getting-started
author: Jane Doe
platform: dev.to
scope_notes: "Covers installation and first project; trimmed from 800 words"
---

The actual blog post content goes here...
```

---

## Step 3: Generate Text (C1-C4)

This step generates 180 texts (15 tasks x 4 conditions x 3 runs) interactively. For each text, the script prints a prompt (system prompt + user message) for you to paste into **Claude Code**, then you paste back the generated response.

```python
from ai_text_quality.config import load_all_tasks, load_style_rules
from ai_text_quality.generate import generate_all
from ai_text_quality.io_utils import save_generated_text

# Load tasks and style rules
tasks = load_all_tasks()
style_rules = load_style_rules()

print(f"Loaded {len(tasks)} tasks")

# Generate all conditions (C1-C4) with 3 runs each
# For each text, you'll be shown the prompt to paste into Claude Code
# and asked to paste back the response.
results = generate_all(tasks, style_rules, runs=3)

# Save all outputs
for gen in results:
    save_generated_text(gen)
    print(f"Saved: {gen.condition}/{gen.task_id}_{gen.run_id}")

print(f"Total generated: {len(results)} texts")
```

**Interactive workflow per text:**

1. The script prints a **system prompt** and a **user message**
2. Open Claude Code (or another LLM chat) and paste the system prompt as context/instructions
3. Paste the user message as the user input
4. Copy the LLM's response
5. Paste it back into the terminal
6. Type `END_OF_RESPONSE` on a new line and press Enter

**What happens internally for each task and run:**

| Condition | Input | Prompt strategy |
|---|---|---|
| C1 `code_only` | Only `code_only` context files | Minimal system prompt |
| C2 `context_rich` | All context files (code + additional) | Minimal system prompt + grounding instructions |
| C3 `style_constrained` | All context files | Persona + anti-pattern rules from `style_rules.yaml` |
| C4 `humanized` | The C2 output text | "Rewrite to sound human, preserve facts" |

**Output location:**
- Markdown files: `data/generated/{condition}/{task_id}_{run_id}.md`
- Metadata sidecar: `data/generated/{condition}/metadata.jsonl`

**Condition directory mapping:**

| Condition label | Directory |
|---|---|
| `code_only` | `data/generated/c1_code_only/` |
| `context_rich` | `data/generated/c2_context_rich/` |
| `style_constrained` | `data/generated/c3_style_constrained/` |
| `humanized` | `data/generated/c4_humanized/` |

**Inspecting outputs:**

```python
from ai_text_quality.io_utils import load_generated_text

# Load a specific output
text = load_generated_text("code_only", "crewai_001", "run_01")
print(text.text[:200])
print(f"Overlap score: {text.overlap_score}")
```

If any output has `overlap_score > 0.15`, consider regenerating it (it borrows too much phrasing from context).

---

## Step 4: Run AI Detection

This step collects AI detection scores for all 195 texts (180 generated + 15 human baselines) by having you paste each text into the **GPTZero** and **Originality.ai** web UIs and enter the reported scores.

```python
import json
from pathlib import Path
from ai_text_quality.detect import run_detection
from ai_text_quality.models import GeneratedText
from ai_text_quality.io_utils import read_jsonl, write_jsonl, read_markdown
from ai_text_quality.paths import GENERATED_DIR, HUMAN_BASELINES_DIR, DETECTION_DIR

# 1. Collect all generated texts from sidecar metadata
all_texts = []
for condition_dir in sorted(GENERATED_DIR.iterdir()):
    if not condition_dir.is_dir():
        continue
    sidecar = condition_dir / "metadata.jsonl"
    for record in read_jsonl(sidecar):
        all_texts.append(GeneratedText(**record))

# 2. Add human baselines as pseudo-GeneratedText objects
for project_dir in sorted(HUMAN_BASELINES_DIR.iterdir()):
    if not project_dir.is_dir():
        continue
    for md_file in sorted(project_dir.glob("*.md")):
        content = read_markdown(md_file)
        # Strip YAML frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            content = parts[2].strip() if len(parts) >= 3 else content
        all_texts.append(GeneratedText(
            task_id=md_file.stem,
            condition="human_baseline",
            run_id="run_01",
            text=content,
            model="human",
            timestamp="",
            token_usage={},
        ))

print(f"Total texts to scan: {len(all_texts)}")

# 3. Run interactive detection
# For each text, you'll be shown the text to paste into GPTZero and
# Originality.ai web UIs, then asked to enter the reported scores.
detection_results = run_detection(all_texts)

# 4. Save results
DETECTION_DIR.mkdir(parents=True, exist_ok=True)
write_jsonl(
    DETECTION_DIR / "detection_results.jsonl",
    [r.model_dump() for r in detection_results],
)

print(f"Saved {len(detection_results)} detection results")
```

**Interactive workflow per text:**

1. The script prints the text to scan
2. **GPTZero:** Go to https://gptzero.me, paste the text, and enter the reported AI-generated probability (0-1)
3. **Originality.ai:** Go to https://originality.ai, paste the text, and enter the reported AI score (0-1)

**Key metrics in each `DetectionResult`:**
- `gptzero_human_prob` -- probability the text is human-written (higher = less detectable = better)
- `gptzero_generated_prob` -- probability the text is AI-generated
- `originality_ai_score` -- Originality.ai AI probability (0-1)
- `originality_human_score` -- Originality.ai human probability (0-1)

---

## Step 5: Run Fact Checking

Score each generated text against its task's gold facts. Literal and regex checks run automatically. Semantic checks are interactive -- the script prints a fact-checking prompt for you to paste into **Claude Code** and enter the verdict.

```python
from ai_text_quality.config import load_all_tasks
from ai_text_quality.factcheck import score_document
from ai_text_quality.io_utils import read_jsonl, write_jsonl
from ai_text_quality.models import GeneratedText
from ai_text_quality.paths import GENERATED_DIR, FACTUAL_DIR

# Build a lookup: task_id -> gold_facts
tasks = load_all_tasks()
task_map = {t.task_id: t for t in tasks}

# Collect all generated texts
all_texts = []
for condition_dir in sorted(GENERATED_DIR.iterdir()):
    if not condition_dir.is_dir():
        continue
    sidecar = condition_dir / "metadata.jsonl"
    for record in read_jsonl(sidecar):
        all_texts.append(GeneratedText(**record))

# Score each document
# Literal and regex checks are automatic.
# Semantic match_type facts show a prompt for you to paste into Claude Code.
fact_results = []
for gen in all_texts:
    task = task_map.get(gen.task_id)
    if not task:
        print(f"Warning: no task definition for {gen.task_id}, skipping")
        continue

    result = score_document(
        text=gen.text,
        task_id=gen.task_id,
        condition=gen.condition,
        run_id=gen.run_id,
        gold_facts=task.gold_facts,
    )
    fact_results.append(result)
    print(f"{gen.condition}/{gen.task_id}/{gen.run_id}: "
          f"hybrid={result.hybrid_slot_accuracy:.2f} "
          f"strict={result.strict_slot_accuracy:.2f}")

# Save results
FACTUAL_DIR.mkdir(parents=True, exist_ok=True)
write_jsonl(
    FACTUAL_DIR / "factcheck_results.jsonl",
    [r.model_dump() for r in fact_results],
)
```

**LLM-judge interactive workflow (semantic facts only):**

1. The script prints a system prompt and user message containing the text and expected fact
2. Paste into Claude Code and get the verdict
3. Paste the response back as a single line (e.g. `CORRECT|The text mentions data processing in paragraph 2`)

**Metrics per document:**
- `hybrid_slot_accuracy` -- fraction of gold facts matched (using appropriate match_type per fact)
- `strict_slot_accuracy` -- fraction matched by literal/regex only (semantic facts scored as MISSING)
- `slot_results` -- per-fact CORRECT / INCORRECT / MISSING verdicts with evidence

---

## Step 6: Extract Linguistic Features

Compute 10 stylometric features for all 195 texts. This step is fully automatic (no manual interaction needed).

```python
from ai_text_quality.linguistic import extract_features
from ai_text_quality.io_utils import read_jsonl, write_jsonl, read_markdown
from ai_text_quality.models import GeneratedText
from ai_text_quality.paths import GENERATED_DIR, HUMAN_BASELINES_DIR, LINGUISTIC_DIR

# Collect all texts (same as Step 4)
all_texts = []
for condition_dir in sorted(GENERATED_DIR.iterdir()):
    if not condition_dir.is_dir():
        continue
    sidecar = condition_dir / "metadata.jsonl"
    for record in read_jsonl(sidecar):
        all_texts.append(GeneratedText(**record))

for project_dir in sorted(HUMAN_BASELINES_DIR.iterdir()):
    if not project_dir.is_dir():
        continue
    for md_file in sorted(project_dir.glob("*.md")):
        content = read_markdown(md_file)
        if content.startswith("---"):
            parts = content.split("---", 2)
            content = parts[2].strip() if len(parts) >= 3 else content
        all_texts.append(GeneratedText(
            task_id=md_file.stem,
            condition="human_baseline",
            run_id="run_01",
            text=content,
            model="human",
            timestamp="",
            token_usage={},
        ))

# Extract features
ling_results = []
for gen in all_texts:
    features = extract_features(gen.text, gen.task_id, gen.condition, gen.run_id)
    ling_results.append(features)
    print(f"{gen.condition}/{gen.task_id}: "
          f"discourse_markers={features.discourse_marker_rate:.2f} "
          f"contractions={features.contraction_rate:.2f}")

# Save results
LINGUISTIC_DIR.mkdir(parents=True, exist_ok=True)
write_jsonl(
    LINGUISTIC_DIR / "linguistic_features.jsonl",
    [r.model_dump() for r in ling_results],
)
```

**The 10 features:**

| Feature | AI signature |
|---|---|
| `sent_len_std` | Low (AI writes uniform sentence lengths) |
| `sent_len_mean` | Tends toward 15-20 words |
| `vocab_diversity` | Lower (repetitive vocabulary) |
| `contraction_rate` | Low (AI avoids contractions) |
| `first_person_rate` | Low (AI rarely uses I/we) |
| `discourse_marker_rate` | High (AI overuses "Furthermore", "Moreover", etc.) |
| `list_density` | High (AI overuses bullet lists) |
| `passive_ratio` | Higher (AI uses more passive voice) |
| `paragraph_len_std` | Low (AI writes uniform paragraph lengths) |
| `specificity_score` | Low (AI includes fewer specific details) |

---

## Step 7: Analysis

Aggregate results, run statistical tests, and generate figures. Use pandas for aggregation and scipy/statsmodels for statistical analysis.

```python
import pandas as pd
import numpy as np
from scipy.stats import wilcoxon
from ai_text_quality.io_utils import read_jsonl
from ai_text_quality.linguistic import compute_style_distance
from ai_text_quality.models import LinguisticFeatures
from ai_text_quality.paths import DETECTION_DIR, FACTUAL_DIR, LINGUISTIC_DIR

# Load all results
detection = pd.DataFrame(read_jsonl(DETECTION_DIR / "detection_results.jsonl"))
factual = pd.DataFrame(read_jsonl(FACTUAL_DIR / "factcheck_results.jsonl"))
linguistic = pd.DataFrame(read_jsonl(LINGUISTIC_DIR / "linguistic_features.jsonl"))

# ── 7a. Summary tables ──────────────────────────────────────────────

# Detection scores by condition
det_summary = detection.groupby("condition").agg(
    gptzero_human_prob_mean=("gptzero_human_prob", "mean"),
    gptzero_human_prob_std=("gptzero_human_prob", "std"),
    originality_human_mean=("originality_human_score", "mean"),
    originality_human_std=("originality_human_score", "std"),
).round(3)
print("Detection Summary:\n", det_summary)

# Factual accuracy by condition
fact_summary = factual.groupby("condition").agg(
    hybrid_acc_mean=("hybrid_slot_accuracy", "mean"),
    hybrid_acc_std=("hybrid_slot_accuracy", "std"),
    strict_acc_mean=("strict_slot_accuracy", "mean"),
    strict_acc_std=("strict_slot_accuracy", "std"),
).round(3)
print("\nFactual Accuracy Summary:\n", fact_summary)

# Linguistic features by condition
feature_cols = [
    "sent_len_std", "sent_len_mean", "vocab_diversity",
    "contraction_rate", "first_person_rate", "discourse_marker_rate",
    "list_density", "passive_ratio", "paragraph_len_std", "specificity_score",
]
ling_summary = linguistic.groupby("condition")[feature_cols].mean().round(3)
print("\nLinguistic Features Summary:\n", ling_summary)

# ── 7b. Style distance from human baseline ──────────────────────────

# Compute mean feature vector for human baselines (C5)
human_rows = linguistic[linguistic["condition"] == "human_baseline"]
baseline_mean = human_rows[feature_cols].mean().to_dict()

# Compute distance for every document
distances = []
for _, row in linguistic.iterrows():
    features = LinguisticFeatures(**row.to_dict())
    dist = compute_style_distance(features, baseline_mean)
    distances.append({
        "task_id": row["task_id"],
        "condition": row["condition"],
        "run_id": row["run_id"],
        "style_distance": dist,
    })
dist_df = pd.DataFrame(distances)
dist_summary = dist_df.groupby("condition")["style_distance"].agg(["mean", "std"]).round(3)
print("\nStyle Distance from Human Baseline:\n", dist_summary)

# ── 7c. Hypothesis tests ────────────────────────────────────────────

# Average replicate-level scores to task-condition means first
det_task_means = detection.groupby(["task_id", "condition"])["gptzero_human_prob"].mean().reset_index()

def paired_wilcoxon(cond_a: str, cond_b: str) -> dict:
    """Paired Wilcoxon test: is cond_b > cond_a on gptzero_human_prob?"""
    a = det_task_means[det_task_means["condition"] == cond_a].set_index("task_id")["gptzero_human_prob"]
    b = det_task_means[det_task_means["condition"] == cond_b].set_index("task_id")["gptzero_human_prob"]
    common = a.index.intersection(b.index)
    if len(common) < 5:
        return {"n": len(common), "note": "too few pairs"}
    stat, p = wilcoxon(b.loc[common], a.loc[common], alternative="greater")
    effect_size = (b.loc[common] - a.loc[common]).mean()
    return {"n": len(common), "statistic": stat, "p_value": p, "mean_diff": effect_size}

# H1: C2 > C1
print("\nH1 (C2 > C1):", paired_wilcoxon("code_only", "context_rich"))

# H2: C3 > C2
print("H2 (C3 > C2):", paired_wilcoxon("context_rich", "style_constrained"))

# H3: C4 > C2 on detection
print("H3 detection (C4 > C2):", paired_wilcoxon("context_rich", "humanized"))

# H4: Report fraction of C1-to-C5 gap closed by C3
c1_mean = det_task_means[det_task_means["condition"] == "code_only"]["gptzero_human_prob"].mean()
c3_mean = det_task_means[det_task_means["condition"] == "style_constrained"]["gptzero_human_prob"].mean()
c5_mean = det_task_means[det_task_means["condition"] == "human_baseline"]["gptzero_human_prob"].mean()
if c5_mean != c1_mean:
    gap_closed = (c3_mean - c1_mean) / (c5_mean - c1_mean)
    print(f"\nH4: C3 closes {gap_closed:.1%} of the C1-to-C5 gap")

# Apply Bonferroni correction: multiply p-values by number of comparisons (3)
```

---

## Step 8: Generate Figures

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Use detection, factual, linguistic, dist_df DataFrames from Step 7

# ── Figure 1: GPTZero human_prob by condition ────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
order = ["code_only", "context_rich", "style_constrained", "humanized", "human_baseline"]
sns.barplot(data=detection, x="condition", y="gptzero_human_prob", order=order, ax=ax, ci=95)
ax.set_ylabel("GPTZero Human Probability")
ax.set_xlabel("Condition")
ax.set_title("AI Detectability by Condition")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig("data/results/summary/fig1_gptzero_by_condition.png", dpi=150)

# ── Figure 2: Originality.ai human score by condition ────────────────
fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(data=detection, x="condition", y="originality_human_score", order=order, ax=ax, ci=95)
ax.set_ylabel("Originality.ai Human Score")
ax.set_xlabel("Condition")
ax.set_title("AI Detectability (Originality.ai) by Condition")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig("data/results/summary/fig2_originality_by_condition.png", dpi=150)

# ── Figure 3: Pareto scatter (detectability vs accuracy) ────────────
merged = detection.merge(factual, on=["task_id", "condition", "run_id"], how="inner")
fig, ax = plt.subplots(figsize=(8, 6))
palette = {"code_only": "#e74c3c", "context_rich": "#3498db",
           "style_constrained": "#2ecc71", "humanized": "#9b59b6"}
for cond, color in palette.items():
    subset = merged[merged["condition"] == cond]
    ax.scatter(subset["gptzero_human_prob"], subset["hybrid_slot_accuracy"],
               label=cond, color=color, alpha=0.6, s=40)
ax.set_xlabel("GPTZero Human Probability (less detectable ->)")
ax.set_ylabel("Hybrid Slot Accuracy")
ax.set_title("Detectability vs Factual Accuracy Trade-off")
ax.legend()
plt.tight_layout()
plt.savefig("data/results/summary/fig3_pareto_scatter.png", dpi=150)

# ── Figure 4: Radar chart of linguistic features ────────────────────
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches

# Normalize features to [0, 1] range for radar
ling_means = linguistic.groupby("condition")[feature_cols].mean()
ling_norm = (ling_means - ling_means.min()) / (ling_means.max() - ling_means.min() + 1e-9)

angles = np.linspace(0, 2 * np.pi, len(feature_cols), endpoint=False).tolist()
angles += angles[:1]  # close the polygon

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
for cond in ["code_only", "context_rich", "style_constrained", "humanized", "human_baseline"]:
    if cond not in ling_norm.index:
        continue
    values = ling_norm.loc[cond].tolist()
    values += values[:1]
    ax.plot(angles, values, label=cond, linewidth=2)
    ax.fill(angles, values, alpha=0.1)
ax.set_xticks(angles[:-1])
ax.set_xticklabels(feature_cols, size=8)
ax.set_title("Linguistic Feature Profiles by Condition")
ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
plt.tight_layout()
plt.savefig("data/results/summary/fig4_radar_features.png", dpi=150)

# ── Figure 5: Feature correlation heatmap ────────────────────────────
corr_cols = feature_cols + ["gptzero_human_prob"]
merged_ling = linguistic.merge(detection[["task_id", "condition", "run_id", "gptzero_human_prob"]],
                                on=["task_id", "condition", "run_id"], how="inner")
corr_matrix = merged_ling[corr_cols].corr()
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax)
ax.set_title("Feature Correlation with Detector Scores")
plt.tight_layout()
plt.savefig("data/results/summary/fig5_feature_correlation.png", dpi=150)

print("Figures saved to data/results/summary/")
```

---

## Step 9: Run Tests

```bash
# From code/ directory
python -m pytest tests/ -v

# Run a specific module's tests
python -m pytest tests/test_linguistic.py -v
python -m pytest tests/test_factcheck.py -v
```

---

## Quick Reference: File Locations

| What | Where |
|---|---|
| Task definitions | `data/tasks/{project}/task_*.yaml` |
| Context materials | `data/context/{project}/{category}/` |
| Human baselines | `data/human_baselines/{project}/` |
| Generated outputs | `data/generated/c{1-4}_*/` |
| Detection results | `data/results/detection/detection_results.jsonl` |
| Fact check results | `data/results/factual/factcheck_results.jsonl` |
| Linguistic features | `data/results/linguistic/linguistic_features.jsonl` |
| Figures | `data/results/summary/fig*.png` |
| Config files | `configs/` |

---

## Troubleshooting

**"spaCy model 'en_core_web_sm' is not installed"**
Run: `python -m spacy download en_core_web_sm`

**High overlap scores (>0.15)**
The generated text borrows too much phrasing from context sources. Regenerate the specific text:
```python
from ai_text_quality.generate import generate_text
from ai_text_quality.config import load_task, load_style_rules
task = load_task("crewai", "task_001")
result = generate_text(task, "context_rich", "run_01")
print(f"Overlap: {result.overlap_score}")
```
