# Instructions: Running the AI Detectability Experiment

---

## Prerequisites

- Python 3.10+
- Access to:
  - **Claude Code** CLI for text generation (Claude Opus 4.6)
  - **Codex CLI** for text generation (GPT 5.4)
  - **Gemini CLI** for text generation (Gemini 3.1)
  - **GPTZero** web UI (https://gptzero.me) for AI detection
  - **Originality.ai** web UI (https://originality.ai) for AI detection

No API keys are required. All LLM generation, fact-checking, and detection interactions happen via copy-paste through CLI tools and web UIs.

---

## Step 0: Environment Setup

```bash
cd code/

# Create a virtual environment and install the package in editable mode
uv venv
source .venv/bin/activate
uv pip install -e .

# Download the spaCy model for linguistic analysis
uv run python -m spacy download en_core_web_sm
```

Verify the installation:

```bash
uv run python -c "from ai_text_quality import Task, GeneratedText; print('OK')"
```

---

## Step 1: Prepare Context Data

Populate the context files referenced by each task YAML in `data/tasks/`. Each task specifies which files it expects under `context_sources`.

Projects: **CrewAI**, **DuckDB**, **LangChain**

### 1a. Clone project repositories

Clone each project's repo into `data/context/{project}/repo/`:

```bash
cd code/
git clone https://github.com/crewAIInc/crewAI data/context/crewai/repo
git clone https://github.com/duckdb/duckdb data/context/duckdb/repo
git clone https://github.com/langchain-ai/langchain data/context/langchain/repo
```

The cloned repos provide README, docs, and source code context. Task YAMLs reference specific files within each repo (e.g., `data/context/crewai/repo/README.md`). After cloning, review the repo structure and update task YAML `code_only` paths to point to the most relevant files for each topic.

### 1b. Collect additional context

| Directory | Content | How to collect |
|---|---|---|
| `data/context/{project}/issues/` | GitHub issue excerpts (title + body + top comments) | `fetch_github.py` |
| `data/context/{project}/community/` | Reddit/HN thread excerpts | `fetch_reddit.py` + `fetch_hn.py` |

Run the fetch scripts for each project (fetches the past week of data):

```bash
cd code/

# GitHub issues (requires GITHUB_TOKEN env var)
uv run python scripts/fetch_github.py --project crewai --since 2026-03-01
uv run python scripts/fetch_github.py --project duckdb --since 2026-03-01
uv run python scripts/fetch_github.py --project langchain --since 2026-03-01

# Reddit posts
uv run python scripts/fetch_reddit.py --project crewai --since 2026-01-01 --fetch-comments
uv run python scripts/fetch_reddit.py --project duckdb --since 2026-01-01 --fetch-comments
uv run python scripts/fetch_reddit.py --project langchain --since 2026-01-01 --fetch-comments

# Hacker News threads
uv run python scripts/fetch_hn.py --project crewai --since 2026-01-01
uv run python scripts/fetch_hn.py --project duckdb --since 2026-01-01
uv run python scripts/fetch_hn.py --project langchain --since 2026-01-01
```

**Preprocessing rules (for issues and community):**
- Scripts automatically strip HTML tags, marketing copy, and canned phrases
- Kept: factual content — version numbers, commands, config details, error messages, trade-offs
- Context is used for factual grounding only, not for borrowing phrasing

Each file is saved as plain markdown.

---

## Step 2: Choose Topics and Collect Human Baselines (C5)

For each project, find 7-8 real engineer-written blog posts or documentation sections on distinct technical topics. These blog posts define the experiment topics — each one becomes a task.

### 2a. Find engineer-written blog posts

**Selection criteria:**
- Written by a named human author
- Published on a credible platform (official blog, Dev.to, Medium, engineering blog)
- Covers a specific, well-scoped technical topic (e.g., setup guide, feature walkthrough, performance comparison)
- Trimmed to 300-500 words if longer

Aim for topic diversity across each project (e.g., getting started, core features, advanced usage, performance, integrations).

### 2b. Create task YAMLs from discovered topics

For each blog post found in 2a, create a corresponding task YAML in `data/tasks/{project}/` using the blog post's topic. See existing task files for the format.

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

All experiment steps are run from a single Jupyter notebook:

```bash
cd code/
uv run jupyter notebook notebooks/experiment.ipynb
```

The notebook covers:
1. **Generation** — Prompts displayed for each CLI tool (Claude Code / Codex / Gemini), paste back responses
2. **Detection** — Paste texts into GPTZero and Originality.ai, enter scores
3. **Fact checking** — Claim extraction + verification via LLM (use a different model as judge)
4. **Linguistic analysis** — Automatic (spaCy)
5. **Statistical analysis** — Hypothesis tests, model comparison, length analysis
6. **Figures** — Bar charts, Pareto scatter, radar, heatmap, model/length plots

---

## Quick Reference: File Locations

| What | Where |
|---|---|
| Task definitions | `data/tasks/{project}/task_*.yaml` |
| Cloned repos | `data/context/{project}/repo/` |
| Additional context | `data/context/{project}/{issues,community}/` |
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
uv run python -m spacy download en_core_web_sm
```

**High overlap scores (>0.15)**

The generated text borrows too much phrasing from context sources. Regenerate via the notebook's "Inspect a specific output" cell.
