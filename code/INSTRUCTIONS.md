# Instructions: Running the AI Detectability Experiment

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

Populate the context files referenced by each task YAML in `data/tasks/`. Each task specifies which files it expects under `context_sources`.

| Directory | Content | How to collect |
|---|---|---|
| `data/context/{project}/code/` | README, doc pages, source file excerpts | Copy from official project docs or repo |
| `data/context/{project}/issues/` | GitHub issue excerpts (title + body + top comments) | Search GitHub issues for topic-related threads |
| `data/context/{project}/community/` | Reddit/HN thread excerpts | Search Reddit/HN for topic discussions |
| `data/context/{project}/releases/` | Relevant changelog entries | Copy from project release notes |
| `data/context/{project}/competitor/` | Competitor docs covering the same concept | Short snippets from similar projects |

**Preprocessing rules:**
- Strip bullet formatting, marketing copy, and canned opening/closing phrases
- Keep factual content: version numbers, commands, config details, error messages, trade-offs
- Context is used for factual grounding only, not for borrowing phrasing

Save each file as plain markdown.

---

## Step 2: Collect Human Baselines (C5)

For each of the 15 task topics, find a real engineer-written blog post or documentation section covering the same subject.

**Selection criteria:**
- Written by a named human author
- Published on a credible platform (official blog, Dev.to, Medium, engineering blog)
- Covers the same technical scope as the task
- Trimmed to 300-500 words if longer

Save each baseline as a markdown file in `data/human_baselines/{project}/` with YAML frontmatter:

```
---
source_url: https://example.com/blog/crewai-getting-started
author: Jane Doe
platform: dev.to
scope_notes: "Covers installation and first project; trimmed from 800 words"
---

The actual blog post content goes here...
```

---

## Steps 3-8: Run the Experiment Notebook

All experiment steps (generation, detection, fact checking, linguistic analysis, statistical analysis, and figure generation) are run from a single Jupyter notebook:

```bash
cd code/
jupyter notebook notebooks/experiment.ipynb
```

The notebook contains cells for each step — run them top-to-bottom. See the markdown headers in the notebook for details on each step.

---

## Running Tests

```bash
cd code/
python -m pytest tests/ -v

# Or a specific module
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
| **Experiment notebook** | `notebooks/experiment.ipynb` |

---

## Troubleshooting

**"spaCy model 'en_core_web_sm' is not installed"**

```bash
python -m spacy download en_core_web_sm
```

**High overlap scores (>0.15)**

The generated text borrows too much phrasing from context sources. Regenerate via the notebook's "Inspect a specific output" cell.
