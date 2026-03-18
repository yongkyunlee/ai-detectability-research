# Research Plan: Context Enrichment and Style Intervention for Reducing AI Detectability in Technical Content

## 1. Motivation

AI-generated technical content is increasingly rejected by practitioners as "AI slop" — shallow, formulaic, and easily identifiable. AI detection tools report >99% accuracy on pure AI output, and 73% of readers say they can spot AI-generated content without tools. Meanwhile, developer tool companies need to publish technical content at scale but cannot afford the reputational cost of publishing text that reads as machine-generated.

The open question is **which interventions actually move the needle**. Is it richer input context (GitHub issues, community discussions, competitor content)? Explicit style constraints (persona prompts, anti-pattern rules)? Post-hoc rewriting? Or is expensive human editing the only path?

This study isolates each intervention through an ablation design, measuring both AI detectability and factual accuracy to map the trade-off frontier. Because large-scale human reading studies are out of scope, detector scores are used as a practical proxy for practitioner-perceived "human-likeness," with that limitation stated explicitly.

### Connection to Course Themes

- **Lecture 03 (Transformers, LLMs, hallucinations):** The core tension — interventions that reduce detectability may introduce hallucinations.
- **Lecture 09 (Evaluation, explainability, trustworthy AI):** The study builds an automated evaluation framework for a quality dimension (naturalness) that currently relies on subjective judgment.

### Practical Contribution

The findings directly inform content generation pipeline design: which enrichment stages to invest in, which style rules to enforce as defaults, and whether post-hoc humanization is safe or dangerous for factual accuracy.

---

## 2. Research Question and Hypotheses

### Research Question

Which content generation strategy most effectively reduces AI detectability, used here as a proxy for practitioner-perceived naturalness, while preserving factual accuracy in technical writing: richer source context, explicit style constraints, post-hoc humanization, or their combination?

### Hypotheses

| ID | Hypothesis | Prediction |
|----|-----------|------------|
| H1 | Context enrichment reduces detectability | C2 (context-rich) scores lower on AI detectors than C1 (code-only), because richer input leads to more specific, less generic output |
| H2 | Style constraints reduce detectability further | C3 (style-constrained) scores lower than C2, because explicit anti-pattern rules suppress the most salient AI tells |
| H3 | Post-hoc humanization reduces detectability but degrades facts | C4 (humanized) scores lowest on detectors but has worse factual precision than C2/C3, because rewriting introduces paraphrasing errors |
| H4 | The combination of context + style closes a substantial portion of the gap to matched human baselines | C3 outperforms C1 and approaches C5 (human baseline) on detector scores without a large factuality penalty |
| H5 | Linguistic features explain detector-proxy scores | A small set of interpretable features (sentence length variance, contraction rate, discourse markers) predicts detector scores and helps explain condition differences |
| H6 | Model choice affects detectability | Different models (Claude Code, GPT 5.4, Gemini 3.1) produce text with different detectability levels, suggesting AI-ness is partially model-specific |
| H7 | Longer content is more detectable | Longer generated texts exhibit more AI patterns (uniform structure, formulaic transitions), making them easier for detectors to flag |

---

## 3. Experimental Design

### 3.1 Generation Conditions

Five conditions form the ablation ladder. Each adds one intervention on top of the previous.

| Condition | Label | Input to the LLM | System prompt strategy |
|-----------|-------|-------------------|----------------------|
| **C1** | `code_only` | Repository README + 1-2 source files | Minimal: "Write a technical blog post about [topic] based on the following documentation." |
| **C2** | `context_rich` | C1 + GitHub issues, changelog entries, community discussions (Reddit/HN threads), competitor content snippets | Same minimal prompt, but with richer context in the user message. Context may be used for facts, terminology, and trade-offs only, not for copying phrasing |
| **C3** | `style_constrained` | Same context as C2 | Enhanced system prompt with persona ("You are a senior engineer writing for your team's blog"), anti-pattern rules (see Section 3.2), and style targets |
| **C4** | `humanized` | Output of C2 (not C3, to isolate the rewrite effect) | A second LLM call: "Rewrite this to sound like a human engineer wrote it. Preserve all technical facts." |
| **C5** | `human_baseline` | N/A — real engineer-written blog posts on the same topics | N/A |

**Why C4 rewrites C2, not C3:** If C4 rewrote C3, the style constraints and the humanization would be confounded. By rewriting C2, we isolate whether a generic "make it sound human" pass achieves the same effect as targeted style rules.

### 3.2 Style Constraint Specification (C3)

The system prompt for C3 includes these rules, derived from known AI text signatures:

```yaml
style_rules:
  persona: "You are a senior backend engineer writing for other engineers. Sound experienced and opinionated, but do not claim personal use or experiences that are not supported by the provided sources."

  sentence_structure:
    - "Vary sentence length. Mix short declarative sentences (5-8 words) with longer explanatory ones (20-30 words)."
    - "Use contractions naturally: don't, it's, we've, wouldn't."
    - "Start some sentences with 'I', 'We', 'So', 'But', or 'And'."

  anti_patterns:
    - "Never start a paragraph with 'In the world of', 'In today's', 'It's worth noting', 'Let's dive in', or 'When it comes to'."
    - "Never use 'Furthermore', 'Moreover', 'It should be noted', 'It's important to note', or 'In conclusion'."
    - "Do not use bullet lists for more than one section. Prefer prose."
    - "Do not hedge with 'arguably', 'it could be said', or 'one might argue'."

  content_rules:
    - "Include at least one specific version number, date, benchmark figure, command, or filename when supported by the provided sources."
    - "Only mention an error message, stack trace, or config snippet if it appears in the provided sources. Do not invent examples."
    - "Include one grounded trade-off judgment based on the provided materials ('X is simpler, but Y gives you...')."
```

### 3.3 Grounding and Contamination Controls

To keep C2/C3 focused on richer context rather than borrowed phrasing, all non-code context is treated as factual/background material only.

- Use context to extract facts, terminology, user pain points, and trade-offs, not reusable prose
- Do not quote or closely paraphrase community or competitor sources unless explicitly marked as a quotation
- Do not reuse contiguous spans longer than 8 words from any context source
- Preprocess community and competitor snippets to remove bullets, marketing copy, and canned opening/closing phrases before prompting
- Run an n-gram overlap check between each generated output and its context bundle; flag outputs above threshold for exclusion or regeneration

### 3.4 Task Set

Each task asks the LLM to write a technical blog section about a specific topic for one open-source project. Reference documentation is provided for factual verification (see Section 4.2).

**Target: 22 tasks across 3 open-source projects.**

| Source project | # Tasks | Example topics | Reference docs |
|---|---|---|---|
| CrewAI | 8 | Installation & setup, Knowledge configuration, Agent tool integration, Project structure, Enterprise deployment | Official docs + release notes |
| DuckDB | 7 | Python client setup, Query performance, Extension system, CSV/Parquet import, Version migration | Official docs + release notes |
| LangChain | 7 | Quickstart, RAG pipelines, Agents & tools, Prompt templates, Memory, Streaming, LCEL | Official docs + release notes |

Example task:

```yaml
task_id: crewai_001
project: crewai
topic: "Getting started with CrewAI: installation and first project"
word_target: "300-500"
reference_docs:
  - data/context/crewai/code/installation.md
context_sources:
  code_only:
    - data/context/crewai/code/installation.md
  additional:
    - data/context/crewai/issues/setup_issues.md
    - data/context/crewai/community/reddit_getting_started.md
```

### 3.5 LLM Configuration

#### Generation Models (Model Comparison Axis)

| CLI Tool | Model | Key | Rationale |
|---|---|---|---|
| Claude Code | Claude Code 4.6 | `claude` | Anthropic's flagship model |
| Codex CLI | GPT 5.4 | `codex` | OpenAI's flagship model |
| Gemini CLI | Gemini 3.1 | `gemini` | Google's flagship model |

All generation happens via CLI tools (no API keys needed). Comparing across models tests whether AI detectability is model-specific or a general property of LLM-generated text.

#### Content Length Axis

| Length | Word target | Rationale |
|---|---|---|
| Short | 150–250 words | Tests whether brevity increases or decreases detectability |
| Medium | 300–500 words | Standard blog section length (baseline) |
| Long | 700–1000 words | Tests whether longer content exhibits more AI patterns |

#### Other Parameters

| Parameter | Value | Rationale |
|---|---|---|
| Temperature | 0.3 | Low enough to reduce run-to-run noise while still allowing stylistic variation |
| Max tokens | 2048 | Sufficient for 1000 words + formatting |
| Runs per condition | 3 per task-condition (`run_01`-`run_03`) | Reduces single-sample noise and supports more stable comparisons |

#### Experimental Matrix

The full factorial (3 CLI tools × 3 lengths × 4 conditions × 22 tasks × 3 runs = 1,620) is large. The recommended design:

| Sub-experiment | Models | Lengths | Conditions | Tasks | Runs | Total texts |
|---|---|---|---|---|---|---|
| **Core ablation** | Claude Code | Medium | C1–C4 | 22 | 3 | 264 |
| **Model comparison** | All 3 | Medium | C1, C3 | 22 | 3 | 396 |
| **Length variation** | Claude Code | All 3 | C1, C3 | 22 | 3 | 396 |

Plus 22 human baselines (C5). Total: ~1,056 texts + 22 baselines = **~1,078 documents**.

### 3.6 Human Baseline Collection (C5)

For each task topic, find a real engineer-written blog post or documentation section covering the same subject. Sources:

- Official project blogs (e.g., `crewai.com/blog`, `duckdb.org/news`)
- Dev.to, Hashnode, Medium posts by practitioners
- Engineering team blogs that reference the project

Selection criteria: written by a named human author, published on a credible platform, covers the same technical scope as the task, and is matched as closely as possible on topic, audience, and genre. Trim to 300-500 words if longer, and record any remaining scope mismatch in metadata.

---

## 4. Validators and Metrics

### 4.1 AI Detection (Detectability Proxy Axis)

| Validator | Access | Output | Role |
|---|---|---|---|
| **GPTZero API** | API key, pay-per-use | Per-document: `completely_generated_prob`, `mixed_prob`, `human_prob`. Per-sentence: classification + probability | Primary proxy detector |
| **Originality.ai API** | API key, $15/mo or pay-per-scan | AI probability score (0-100), per-paragraph breakdown | Secondary proxy detector / cross-check |

**Interpretation note:** These are proxy measures for practitioner-perceived naturalness, not direct evidence of human reader preference.

**Primary metric:** `human_prob` from GPTZero (higher = less detectable = better).
**Secondary metric:** `(100 - ai_score)` from Originality.ai, normalized to same direction.
**Agreement metric:** Cohen's kappa between the two detectors' binary classifications (AI vs human at 50% threshold).

### 4.2 Factual Accuracy (Accuracy Axis) — Claim-Based Verification

Instead of pre-defined gold fact tables, factual accuracy is measured by extracting and verifying claims from the generated text (FActScore-style). This measures **precision** ("are the claims made correct?") rather than recall ("did it mention required facts?").

| Step | Implementation | Output |
|---|---|---|
| **1. Claim extraction** | LLM extracts all atomic factual claims from the generated text (version numbers, commands, config details, behavioral descriptions, compatibility) | List of claims with source sentences |
| **2. Claim verification** | A separate LLM call checks each claim against the task's reference documentation | Per-claim verdict: CORRECT / INCORRECT / UNVERIFIABLE |
| **3. Scoring** | Compute precision over verifiable claims | `factual_precision = correct / (correct + incorrect)` |

**Judge models:** Use a different model as judge than the one that generated the text to avoid self-bias. E.g., if text was generated by GPT 5.4, use Claude Code 4.6 as judge.

**Primary metric:** Factual precision (correct / (correct + incorrect)).
**Secondary metrics:** Total claims count (measures information density), incorrect claim count (raw error count), unverifiable rate.

**Why this replaces gold fact tables:** Gold facts extracted from docs may not be naturally covered by a blog post, biasing the metric toward exhaustive/comprehensive (AI-like) text and against naturally-written text that omits some details. Claim-based verification measures correctness of what was actually written.

### 4.3 Linguistic Features (Interpretability Axis)

Computed per document. These explain *why* a condition is more or less detectable.

| Feature | Computation | Known AI signature |
|---|---|---|
| `sent_len_std` | Std dev of word counts per sentence | AI: low variance (uniform length) |
| `sent_len_mean` | Mean words per sentence | AI: tends toward 15-20 |
| `vocab_diversity` | Type-token ratio (unique words / total words) on first 200 words | AI: lower diversity |
| `contraction_rate` | Contractions used / opportunities for contractions | AI: avoids contractions |
| `first_person_rate` | (I, we, my, our, me, us) / total words | AI: low first-person usage |
| `discourse_marker_rate` | Count of flagged phrases ("Furthermore", "Moreover", "It's worth noting", etc.) / total sentences | AI: high rate |
| `list_density` | List items / total paragraphs | AI: overuses lists |
| `passive_ratio` | Passive voice sentences / total sentences (via spaCy) | AI: more passive |
| `paragraph_len_std` | Std dev of word counts per paragraph | AI: uniform paragraph length |
| `specificity_score` | (Named entities + numbers) / total sentences | AI: fewer specific references |

**Composite metric:** Cosine distance of the 10-feature vector from the mean C5 (human baseline) vector — "how far from matched human style."

### 4.4 Summary Metrics Table

| Metric | Type | Direction | Primary/Secondary |
|---|---|---|---|
| GPTZero human_prob | Detectability proxy | Higher = better | Primary |
| Originality.ai human score | Detectability proxy | Higher = better | Secondary |
| Factual precision | Factual | Higher = better | Primary |
| Total claims count | Factual (density) | Descriptive | Secondary |
| Incorrect claim count | Factual (errors) | Lower = better | Secondary |
| Style distance from human | Interpretability | Lower = better | Primary |
| Per-feature analysis | Interpretability | Varies | Exploratory |

---

## 5. Repository Structure

```
ai-text-quality/
├── pyproject.toml
├── README.md
├── configs/
│   ├── projects/                   # Per-project config (like repos/ in gensearch-eval)
│   │   ├── crewai.yaml
│   │   └── duckdb.yaml
│   ├── conditions.yaml             # C1-C4 prompt templates and rules
│   ├── style_rules.yaml            # Anti-patterns, persona templates (used by C3)
│   └── validators.yaml             # API keys placeholder, thresholds, feature list
├── data/
│   ├── tasks/                      # Task definitions with reference docs
│   │   ├── crewai/
│   │   │   ├── task_001.yaml
│   │   │   ├── task_002.yaml
│   │   │   └── ...
│   │   └── duckdb/
│   │       └── ...
│   ├── context/                    # Rich context materials per project
│   │   ├── crewai/
│   │   │   ├── code/               # README, source files (C1 input)
│   │   │   ├── issues/             # GitHub issue excerpts
│   │   │   ├── community/          # Reddit/HN thread excerpts
│   │   │   ├── releases/           # Changelog entries
│   │   │   └── competitor/         # Competitor content snippets
│   │   └── duckdb/
│   │       └── ...
│   ├── human_baselines/            # C5: real engineer-written posts
│   │   ├── crewai/
│   │   │   ├── baseline_001.md
│   │   │   └── ...
│   │   └── duckdb/
│   │       └── ...
│   ├── generated/                  # LLM outputs organized by condition
│   │   ├── c1_code_only/
│   │   │   ├── crewai_001_run_01.md
│   │   │   └── ...
│   │   ├── c2_context_rich/
│   │   ├── c3_style_constrained/
│   │   └── c4_humanized/
│   └── results/                    # Validator outputs and aggregated metrics
│       ├── detection/              # GPTZero + Originality.ai raw responses
│       ├── factual/                # Claim extraction + verification results
│       ├── linguistic/             # Feature vectors per document
│       └── summary/                # Aggregated tables, figures
├── src/
│   └── ai_text_quality/
│       ├── __init__.py
│       ├── models.py               # Pydantic models for tasks, results, features
│       ├── config.py               # Load YAML configs
│       ├── paths.py                # Path constants and helpers
│       ├── generate.py             # Build prompts per condition, call LLM API
│       ├── detect.py               # GPTZero + Originality.ai API wrappers
│       ├── factcheck.py            # Claim extraction + verification (FActScore-style)
│       ├── linguistic.py           # Compute 10 linguistic features per document
│       └── io_utils.py             # JSONL / YAML / markdown read/write helpers
├── notebooks/
│   ├── 01_task_design.ipynb        # Define tasks, inspect gold facts, preview context
│   ├── 02_generate.ipynb           # Run generation for all conditions, inspect outputs
│   ├── 03_validate.ipynb           # Run all validators, inspect per-document results
│   ├── 04_analysis.ipynb           # Aggregate metrics, statistical tests, figures
│   └── 05_examples.ipynb           # Cherry-picked examples for slides (side-by-side)
```

---

## 6. Implementation Plan

### Phase 1: Scaffolding and Data Preparation

**Goal:** Repository setup, task definitions, context collection, contamination controls, human baselines.

#### 1.1 Repository Setup
- Initialize repo with `pyproject.toml`, directory structure, `.gitignore`
- Dependencies: `pydantic`, `pyyaml`, `spacy`, `pandas`, `matplotlib`, `seaborn`, `scipy`, `statsmodels`, `jupyter`
- Pydantic models in `models.py`:
  - `Task` (task_id, project, topic, word_target, reference_docs, context_sources)
  - `Claim` (claim_id, text, source_sentence)
  - `ClaimVerdict` (claim_id, claim_text, verdict: CORRECT | INCORRECT | UNVERIFIABLE, evidence)
  - `GeneratedText` (task_id, condition, run_id, text, model, timestamp, token_usage, overlap_score, word_target)
  - `DetectionResult` (task_id, condition, run_id, model, word_target, gptzero_human_prob, gptzero_mixed_prob, gptzero_generated_prob, gptzero_sentences, originality_score, originality_paragraphs)
  - `FactCheckResult` (task_id, condition, run_id, model, word_target, claims: list[ClaimVerdict], total_claims, correct_claims, incorrect_claims, unverifiable_claims, factual_precision)
  - `LinguisticFeatures` (task_id, condition, run_id, model, word_target, sent_len_std, sent_len_mean, vocab_diversity, contraction_rate, first_person_rate, discourse_marker_rate, list_density, passive_ratio, paragraph_len_std, specificity_score)

#### 1.2 Task Design (Notebook 01)
- Define 22 tasks across CrewAI, DuckDB, and LangChain
- For each task: write the topic, list reference docs for fact verification, list context source paths
- Validate: each task has at least one reference doc, context files exist, no overlap between tasks

#### 1.3 Context Collection
- **Code/docs:** Copy relevant sections from existing `data/raw/` in gensearch-eval, or fetch from public repos
- **GitHub issues:** For each project, find 3-5 real issues related to each task topic. Save as markdown excerpts (title, body, top comments) in `data/context/{project}/issues/`
- **Community:** Search Reddit/HN for threads about each topic. Save 2-3 relevant thread excerpts per task
- **Competitor:** For each topic, find a short snippet from a competitor project's docs covering the same concept
- **Releases:** Relevant changelog entries
- **Preprocessing:** Strip quotes, bullets, and boilerplate phrasing from community/competitor sources before they are added to the prompt context bundle
- **Validation:** Record source URLs and run overlap checks so generated text that is too close to a context source can be regenerated or excluded

#### 1.4 Human Baseline Collection
- For each task topic, find 1 real blog post or tutorial section written by a human engineer
- Trim to 300-500 words covering the same scope
- Record source URL and author in metadata

### Phase 2: Generation Pipeline

**Goal:** Generate AI texts across all conditions, models, and lengths, plus collect 15 human baselines.

#### 2.1 Implement `generate.py`
- `build_prompt(task, condition, style_rules, word_target)` — returns (system_prompt, user_message)
- `generate_text(task, condition, run_id, style_rules, model_key, word_target)` — interactive generation (user pastes into target model UI)
- `generate_humanized(source_text, run_id, model_key, word_target)` — C4 rewrite call
- `generate_all(tasks, style_rules, runs, model_keys, word_targets)` — batch generation across all axes
- Embed hard instructions for C2-C4: use context for factual grounding only, do not copy wording from context sources
- Compute and save overlap metrics against the task's context bundle after each generation

#### 2.2 Run Generation (Notebook 02)
- **Core ablation:** Loop over tasks × runs × conditions C1-C4 with Claude Code at medium length
- **Model comparison:** Loop over tasks × runs × {C1, C3} × {Claude Code, GPT 5.4, Gemini 3.1} at medium length
- **Length variation:** Loop over tasks × runs × {C1, C3} × {short, medium, long} with Claude Code
- For each text, the prompt is displayed for the user to paste into the appropriate model's UI
- Save outputs to `data/generated/{condition}/{task_id}_{model}_{length}_{run_id}.md`
- Save generation metadata (model, word_target, tokens, timestamp, overlap score) as JSONL sidecar

### Phase 3: Validation Pipeline

**Goal:** Run all validators on all 195 texts (180 generated + 15 human baselines).

#### 3.1 Implement `detect.py`
- `detect_gptzero(text: str) -> dict` — calls GPTZero API, returns full response
- `detect_originality(text: str) -> dict` — calls Originality.ai API, returns full response
- `run_detection(texts: list[GeneratedText]) -> list[DetectionResult]` — batch wrapper with rate limiting

**API details:**

GPTZero:
- Endpoint: `POST https://api.gptzero.me/v2/predict/text`
- Auth: `x-api-key` header
- Input: `{"document": text}`
- Output: `completely_generated_prob`, `mixed_prob`, `human_prob`, per-sentence classifications

Originality.ai:
- Endpoint: `POST https://api.originality.ai/api/v1/scan/ai`
- Auth: `X-OAI-API-KEY` header
- Input: `{"content": text}`
- Output: `score.ai` (0-1), `score.original` (0-1), per-paragraph breakdown

#### 3.2 Implement `factcheck.py` (Claim-Based Verification)
- `build_extract_prompt(text) -> (system, user)` — generates prompt for LLM to extract atomic factual claims
- `parse_extracted_claims(raw_response) -> list[Claim]` — parses claim extraction output
- `build_verify_prompt(claims, reference_text) -> (system, user)` — generates prompt for LLM to verify claims against docs
- `parse_verification_response(raw_response, claims) -> list[ClaimVerdict]` — parses verification output
- `compute_factual_precision(verdicts) -> float` — correct / (correct + incorrect)
- `score_document(text, task_id, condition, run_id, reference_text, model, word_target) -> FactCheckResult`
- Use a different LLM as judge than the generator to avoid self-bias

#### 3.3 Implement `linguistic.py`
- `extract_features(text: str) -> LinguisticFeatures` — computes all 10 features
- Uses spaCy (`en_core_web_sm`) for sentence splitting, POS tagging, NER, dependency parsing
- Contraction detection via regex
- Discourse marker detection via curated keyword list

#### 3.4 Run Validation (Notebook 03)
- Run detection on all texts (~750 total) via GPTZero and Originality.ai web UIs
- Run claim-based fact checking on all generated texts (extract claims, verify against reference docs)
- Run linguistic feature extraction on all texts
- Save all results to `data/results/` as JSONL
- Display per-document results inline

### Phase 4: Analysis

**Goal:** Aggregate results, test hypotheses, generate figures.

#### 4.1 Analysis (Notebook 04)

**Aggregate tables:**
- Mean and std of GPTZero `human_prob` by condition
- Mean and std of Originality.ai human score by condition
- Mean factual precision by condition
- Mean total claims count by condition (information density)
- Mean linguistic feature values by condition (10-feature table)
- Style distance from C5 by condition
- **Model comparison:** Mean detectability by model (across conditions)
- **Length variation:** Mean detectability by word target (across conditions)

**Statistical tests:**
- Average replicate-level scores to task-condition means, then run paired Wilcoxon signed-rank tests between adjacent conditions (C1 vs C2, C2 vs C3, C2 vs C4)
- With 15 paired tasks per comparison, power is still limited, so report effect sizes and confidence intervals alongside p-values
- Bonferroni correction for multiple comparisons
- For H5, fit regression with task fixed effects or cluster-robust standard errors by task rather than treating all document rows as independent
- **Model comparison:** Kruskal-Wallis test across models, pairwise comparisons
- **Length variation:** Spearman correlation between word count and detectability score

**Figures:**
1. **Bar chart:** Mean GPTZero human_prob by condition (with error bars), C5 as reference line
2. **Bar chart:** Mean Originality.ai human score by condition
3. **Scatter plot:** Detectability vs factual precision per document, colored by condition — the Pareto frontier
4. **Radar chart:** Mean linguistic features by condition (normalized), showing which features each intervention changes
5. **Heatmap:** Feature correlation with detector scores (which features predict detectability?)
6. **Bar chart:** Detectability by model (Claude Code vs GPT 5.4 vs Gemini 3.1) for C1 and C3
7. **Line plot:** Detectability by content length (short/medium/long) for C1 and C3
8. **Table:** Per-task breakdown showing where conditions diverge most

**Hypothesis testing:**
- H1: paired test C2 > C1 on human_prob
- H2: paired test C3 > C2 on human_prob
- H3: paired test C4 > C2 on human_prob AND C4 <= C2 on factual precision
- H4: report the fraction of the C1-to-C5 gap recovered by C3 on detector scores as a descriptive effect size, not a hard pass/fail threshold
- H5: regression of human_prob ~ 10 features with task controls, report R² and top-3 coefficients
- H6 (new): model comparison — are some models inherently less detectable?
- H7 (new): length effect — does content length correlate with detectability?

#### 4.2 Examples (Notebook 05)
- Side-by-side display of C1 through C5 for 2-3 selected tasks
- Highlight specific sentences where AI tells appear or disappear across conditions
- Show a case where C4 humanization introduced a factual error
- Show a case where C3 style rules eliminated a discourse marker without losing content

---

## 7. Slide Deck Outline (10-Minute Presentation)

| Slide | Content | Duration |
|---|---|---|
| 1. tl;dr | Problem: AI text is detectable and rejected. Method: 5-condition ablation + model/length axes. Key finding: [TBD]. | 30s |
| 2. Motivation | AI slop stats (73% spot it, 9x growth in complaints), industry impact on developer content | 1m |
| 3. Literature Review | Detection methods, paraphrasing attacks, detector biases, citation metrics | 1.5m |
| 4. Research Question & Design | RQ, 5 conditions table, 3 CLI tools, 3 lengths, task set | 1.5m |
| 5. Methodology | Detection + claim-based fact checking + linguistic features, metrics | 1m |
| 6. Results: Detectability | Bar charts of detector scores by condition, statistical tests | 1m |
| 7. Results: Trade-off | Pareto scatter (detectability vs factual precision) | 1m |
| 8. Results: Model Comparison | Detectability by model for C1 and C3 | 0.5m |
| 9. Results: Length Effect | Detectability by content length | 0.5m |
| 10. Results: Features | Radar chart, regression, which features matter most | 1m |
| 11. Code & Demo | Repo structure, example C1 vs C3 | 0.5m |
| 12. YouTube Demo Link | Link to pre-recorded notebook walkthrough | — |

---

## 8. Literature

| Paper | Year | Relevance |
|---|---|---|
| Kirchenbauer et al., "A Watermark for Large Language Models" | 2023 | Detection-side: what statistical properties make text identifiable as AI |
| Sadasivan et al., "Can AI-Generated Text Be Reliably Detected?" | 2023 | Shows paraphrasing attacks reduce detector accuracy — directly relevant to C4 |
| Liang et al., "GPT Detectors Are Biased Against Non-Native English Writers" | 2023 | Detector reliability caveats; motivates using multiple detectors |
| Krishna et al., "Paraphrasing Evades Detectors of AI-Generated Text" | 2024 | Systematic study of rewriting as evasion — informs C4 design |
| Mitchell et al., "DetectGPT: Zero-Shot Machine-Generated Text Detection" | 2023 | Foundational detection method; explains log-probability curvature approach |
| Gao et al., "Enabling LLMs to Generate Text with Citations" (ALCE) | 2023 | Citation quality metrics reusable for factual evaluation |
| Liu et al., "Evaluating Verifiability in Generative Search Engines" | 2023 | Shows surface quality ≠ citation support — motivates measuring both axes |

---

## 9. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Small sample size (22 tasks) limits statistical power | Cannot detect small effect sizes | Use 3 runs per condition, aggregate to task-level comparisons, and report effect sizes and confidence intervals, not just p-values. Frame as exploratory. |
| Detector APIs may change behavior between runs | Non-reproducible results | Pin API versions, save raw API responses, run all detection in a single batch session |
| GPTZero/Originality.ai may not expose per-sentence data for short texts | Lose granularity | Ensure texts are >250 words (both APIs recommend this minimum) |
| Human baselines may not match task scope exactly | C5 comparison is imprecise | Select baselines carefully, match topic/audience/genre where possible, document scope differences, and treat C5 gap-closing as descriptive rather than absolute |
| LLM-as-judge for fact checking may be unreliable | Inconsistent claim extraction or verification across runs | Use structured prompts, run judge multiple times for key samples, report inter-run agreement |
| Style rules in C3 could overfit known detector patterns | Trivially high scores that don't generalize | Use two independent detectors; include linguistic features as an interpretability check beyond detector gaming |
| Rich context may leak phrasing from community or competitor sources | Artificially improved detector scores through borrowed prose | Treat context as factual input only, strip boilerplate before prompting, and exclude/regenerate outputs with high n-gram overlap |
| Detector scores are only a proxy for practitioner judgment | Conclusions may overstate real reader perception | State the proxy limitation explicitly throughout and frame results as detector-facing evidence, not direct human preference evidence |

---

## 10. Dependencies and API Keys

| Dependency | Purpose | Install |
|---|---|---|
| *(none for generation)* | Text generation via CLI tools (Claude Code, Codex CLI, Gemini CLI) | N/A — interactive copy-paste |
| `pydantic` | Data models | `pip install pydantic` |
| `pyyaml` | Config loading | `pip install pyyaml` |
| `spacy` + `en_core_web_sm` | Linguistic feature extraction | `pip install spacy && python -m spacy download en_core_web_sm` |
| `pandas` | Data aggregation | `pip install pandas` |
| `matplotlib` + `seaborn` | Figures | `pip install matplotlib seaborn` |
| `scipy` | Statistical tests (Wilcoxon) | `pip install scipy` |
| `statsmodels` | Regression with task controls / robust SEs | `pip install statsmodels` |
| `jupyter` | Notebook execution | `pip install jupyter` |

**Environment variables needed:**
- None required — all interactions happen via CLI tools (Claude Code, Codex CLI, Gemini CLI) and web UIs (GPTZero, Originality.ai)

---

## 11. Execution Sequence

```
Stage 1: Scaffolding
         ├── Repository setup, pyproject.toml, directory structure
         ├── Pydantic models, config loading, path helpers
         ├── Task definitions (22 tasks with reference docs)
         └── Context collection (issues, community, competitor snippets)

Stage 2: Generation + Human Baselines
         ├── Implement generate.py (multi-model, multi-length support)
         ├── Core ablation: C1-C4 × 22 tasks × 3 runs with Claude Code (medium)
         ├── Model comparison: C1,C3 × 22 tasks × 3 runs × 3 CLI tools (medium)
         ├── Length variation: C1,C3 × 22 tasks × 3 runs × 3 lengths (Claude Code)
         ├── Collect 15 human baselines
         └── Quick manual inspection of outputs

Stage 3: Validation
         ├── Implement detect.py (GPTZero + Originality.ai wrappers)
         ├── Implement factcheck.py (claim extraction + verification)
         ├── Implement linguistic.py (10 features)
         ├── Notebook 03: run all validators, save results
         └── Tests for each validator module

Stage 4: Analysis + Presentation
         ├── Notebook 04: aggregate metrics, statistical tests, figures
         ├── Notebook 05: example comparisons for slides
         ├── Build slide deck (10+ slides)
         ├── Record YouTube demo (notebook walkthrough)
         └── Final PDF
```
