# Context Enrichment and Style Intervention for Reducing AI Detectability in Technical Content

**Yong Kyun Lee**
Mini Research Project — March 2025

---

## tl;dr

**Problem:** AI-generated technical content is easily detected and dismissed as "AI slop" — 73% of readers say they can spot it, and detection tools report >99% accuracy on raw AI output.

**Method:** 5-condition ablation study isolating the effect of context enrichment, style constraints, and post-hoc humanization on AI detectability and factual accuracy across 15 technical writing tasks.

**Key Results:**
- Style constraints (C3) reduced AI detection by **[X]%** over baseline while preserving **[Y]%** factual accuracy
- Post-hoc humanization (C4) achieved lowest detector scores but introduced factual errors in **[Z]%** of cases
- Context enrichment + style rules closed **[W]%** of the gap to human baselines without sacrificing accuracy

---

## Motivation

### The "AI Slop" Problem in Technical Content

- AI-generated content production has grown **9x** in the past year
- **73%** of practitioners say they can identify AI-generated text without tools
- AI detectors (GPTZero, Originality.ai) report **>99%** accuracy on unmodified AI output
- Developer tool companies need content at scale but face reputational costs from detectable AI text

### The Open Question

Which interventions actually reduce detectability?

| Strategy | Promise | Risk |
|---|---|---|
| Richer input context | More specific, less generic output | May leak source phrasing |
| Explicit style constraints | Suppress known AI tells | May overfit detector patterns |
| Post-hoc humanization | Broad rewrite | May degrade factual accuracy |
| Human editing | Gold standard | Expensive, doesn't scale |

### Course Connection
- **Lecture 03 (Transformers & LLMs):** Interventions that reduce detectability may introduce hallucinations
- **Lecture 09 (Evaluation & Trustworthy AI):** Building automated evaluation for naturalness, a quality dimension that currently relies on subjective judgment

---

## Literature Review

### AI Text Detection

| Paper | Key Contribution |
|---|---|
| **Mitchell et al. (2023)** — DetectGPT | Zero-shot detection via log-probability curvature; foundational method behind modern detectors |
| **Kirchenbauer et al. (2023)** — Watermarking LLMs | Identifies statistical properties that make AI text identifiable (token distribution patterns) |

### Evasion & Robustness

| Paper | Key Contribution |
|---|---|
| **Sadasivan et al. (2023)** — Can AI Text Be Reliably Detected? | Shows paraphrasing attacks reduce detector accuracy significantly — motivates our C4 condition |
| **Krishna et al. (2024)** — Paraphrasing Evades Detectors | Systematic study of rewriting as evasion; informs humanization strategy design |
| **Wang et al. (2025)** — Humanizing the Machine (ICLR 2025) | Proxy attack (HUMPA) uses DPO-fine-tuned smaller model to make LLM output evade detectors in both white-box and black-box settings — extends evasion beyond simple paraphrasing |

### Detector Limitations & Evaluation

| Paper | Key Contribution |
|---|---|
| **Liang et al. (2023)** — GPT Detectors Are Biased | Detectors biased against non-native English writers; motivates using multiple detectors |
| **Wu et al. (2024)** — DetectRL (NeurIPS 2024) | Benchmark showing SOTA detectors underperform in real-world scenarios with adversarial modifications, spelling noise, and human revisions — motivates robust evaluation |
| **Gao et al. (2023)** — ALCE | Citation quality metrics reusable for factual evaluation of generated text |
| **Liu et al. (2023)** — Verifiability in Gen. Search | Surface quality does not equal factual support — motivates measuring both detectability and accuracy |

### Stylistic Features & Interpretability

| Paper | Key Contribution |
|---|---|
| **Rivera Soto et al. (2025)** — Distinct Style Persists (NeurIPS 2025 Spotlight) | Even models optimized to fool detectors retain identifiable stylistic signatures — supports using linguistic features as a robust detection axis (directly relevant to H5) |

### Gap This Study Addresses
Prior work focuses on detection vs. evasion as a binary arms race. No study systematically isolates which *content generation pipeline decisions* (context, style rules, rewriting) move detectability while tracking factual accuracy as a co-metric.

---

## Experimental Design

### 5-Condition Ablation Ladder

Each condition adds one intervention on top of the previous:

| Condition | Label | What Changes | Input |
|---|---|---|---|
| **C1** | `code_only` | Baseline | README + source files only |
| **C2** | `context_rich` | + Rich context | C1 + GitHub issues, community threads, competitor docs |
| **C3** | `style_constrained` | + Style rules | C2 context + persona prompt, anti-pattern rules, style targets |
| **C4** | `humanized` | + Rewrite pass | C2 output rewritten with "sound human" prompt |
| **C5** | `human_baseline` | Ground truth | Real engineer-written blog posts on same topics |

**Why C4 rewrites C2, not C3:** Isolates the rewrite effect from style constraints — avoids confounding two interventions.

### Task Set
- **15 tasks** across 2 open-source projects (CrewAI, DuckDB)
- Each task: write a 300–500 word technical blog section
- Each task has a **gold fact table** (3–7 required facts: version numbers, commands, file names)
- **3 runs per condition** → 180 generated texts + 15 human baselines = **195 total documents**

---

## Style Constraint Design (C3)

### Persona
> "You are a senior backend engineer writing for other engineers. Sound experienced and opinionated."

### Sentence Structure Rules
- Vary sentence length: mix short (5–8 words) with longer (20–30 words)
- Use contractions naturally: *don't*, *it's*, *we've*
- Start some sentences with *I*, *We*, *So*, *But*, or *And*

### Anti-Pattern Rules (Suppress Known AI Tells)
- **Never** start with: *"In the world of"*, *"In today's"*, *"Let's dive in"*
- **Never** use: *"Furthermore"*, *"Moreover"*, *"It's important to note"*, *"In conclusion"*
- **No** excessive bullet lists — prefer prose
- **No** hedging: *"arguably"*, *"one might argue"*

### Content Rules
- Include at least one specific version number, date, or command from sources
- Only mention errors/configs that appear in provided sources
- Include one grounded trade-off judgment

---

## Methodology: Three Evaluation Axes

### Axis 1: AI Detectability (Proxy for Naturalness)

| Detector | Metric | Direction |
|---|---|---|
| **GPTZero** (primary) | `human_prob` per document | Higher = less detectable |
| **Originality.ai** (secondary) | `100 - ai_score` | Higher = less detectable |
| Cross-check | Cohen's kappa between detectors | Agreement measure |

### Axis 2: Factual Accuracy

| Method | How It Works |
|---|---|
| **Hybrid slot accuracy** (primary) | Per gold fact: `literal`/`regex` → automatic match; `semantic` → LLM judge |
| **Strict slot accuracy** (secondary) | Literal/regex matches only |
| **LLM judge audit** | Full rubric-based check for CORRECT / INCORRECT / MISSING per slot |

### Axis 3: Linguistic Features (Interpretability)

10 features computed per document to explain *why* a condition is more/less detectable:

`sent_len_std` · `sent_len_mean` · `vocab_diversity` · `contraction_rate` · `first_person_rate` · `discourse_marker_rate` · `list_density` · `passive_ratio` · `paragraph_len_std` · `specificity_score`

**Composite metric:** Cosine distance of 10-feature vector from mean C5 (human) vector.

---

## Results: AI Detectability

### GPTZero Human Probability by Condition

```
           Mean human_prob (higher = less detectable)
           ┌──────────────────────────────────────────────────┐
C1         │████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ [0.XX]
C2         │████████████░░░░░░░░░░░░░░░░░░░░░░░░│ [0.XX]
C3         │████████████████████░░░░░░░░░░░░░░░░│ [0.XX]
C4         │██████████████████████░░░░░░░░░░░░░░│ [0.XX]
C5 (human) │████████████████████████████████████│ [0.XX]
           └──────────────────────────────────────────────────┘
```

### Originality.ai Human Score by Condition

```
           Mean human score (higher = less detectable)
           ┌──────────────────────────────────────────────────┐
C1         │██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ [XX]
C2         │██████████░░░░░░░░░░░░░░░░░░░░░░░░░░│ [XX]
C3         │██████████████████░░░░░░░░░░░░░░░░░░│ [XX]
C4         │████████████████████░░░░░░░░░░░░░░░░│ [XX]
C5 (human) │████████████████████████████████████│ [XX]
           └──────────────────────────────────────────────────┘
```

### Statistical Tests (Paired Wilcoxon, n=15 tasks)

| Comparison | Hypothesis | Effect Size | p-value |
|---|---|---|---|
| C2 > C1 | H1: Context helps | [d = X.XX] | [p = X.XX] |
| C3 > C2 | H2: Style rules help further | [d = X.XX] | [p = X.XX] |
| C4 > C2 | H3: Humanization helps | [d = X.XX] | [p = X.XX] |

---

## Results: Detectability vs. Factual Accuracy Trade-off

### The Pareto Frontier

```
  Factual Accuracy (hybrid slot %)
  1.0 ┤
      │         ◆ C5
      │    ● C3
  0.9 ┤    ● C2
      │  ● C1
      │
  0.8 ┤
      │              ▲ C4
  0.7 ┤
      │
      └────┬─────┬─────┬─────┬─────┬──
          0.0   0.2   0.4   0.6   0.8  1.0
            GPTZero human_prob (less detectable →)

  ● Context/Style conditions   ▲ Humanized   ◆ Human baseline
```

### Key Findings

| Metric | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|
| GPTZero human_prob | [X.XX] | [X.XX] | [X.XX] | [X.XX] | [X.XX] |
| Hybrid slot accuracy | [X.XX] | [X.XX] | [X.XX] | [X.XX] | — |
| Style distance from human | [X.XX] | [X.XX] | [X.XX] | [X.XX] | 0.00 |

- **H3 result:** C4 achieves [lowest/near-lowest] detectability but factual accuracy drops by [X]% — humanization introduces paraphrasing errors
- **H4 result:** C3 closes **[W]%** of the C1→C5 gap on detector scores with only **[V]%** factual accuracy loss
- **Takeaway:** Context + style rules offer the best accuracy-preserving path to reduced detectability

---

## Results: Linguistic Feature Analysis

### Feature Profiles by Condition (Normalized to Human Baseline)

```
                    C1    C2    C3    C4    C5(human)
sent_len_std       [lo]  [lo]  [mid] [mid] [hi]
contraction_rate   [lo]  [lo]  [hi]  [mid] [hi]
first_person_rate  [lo]  [lo]  [mid] [mid] [hi]
discourse_markers  [hi]  [hi]  [lo]  [mid] [lo]
list_density       [hi]  [mid] [lo]  [mid] [lo]
vocab_diversity    [lo]  [mid] [mid] [mid] [hi]
passive_ratio      [hi]  [mid] [lo]  [mid] [lo]
specificity_score  [lo]  [mid] [mid] [mid] [hi]
```

### Regression: Which Features Predict Detectability? (H5)

| Feature | Coefficient | p-value |
|---|---|---|
| `discourse_marker_rate` | [−X.XX] | [X.XX] |
| `contraction_rate` | [+X.XX] | [X.XX] |
| `sent_len_std` | [+X.XX] | [X.XX] |

**Model R² = [X.XX]** — a small set of interpretable features explains [X]% of variance in detector scores.

### Interpretation
- **C3 style rules directly target the top predictive features** (discourse markers, contractions, sentence variance)
- Detector scores are not a black box — they track measurable stylistic patterns
- This suggests targeted style interventions can be *principled*, not just heuristic

---

## Code & Implementation

### Repository Structure

```
ai-detectability-research/
├── configs/
│   ├── conditions.yaml        # C1-C4 prompt templates
│   ├── style_rules.yaml       # Anti-patterns, persona (C3)
│   └── validators.yaml        # API config, thresholds
├── data/
│   ├── tasks/                 # 15 task definitions + gold facts
│   ├── context/               # Rich context per project
│   ├── human_baselines/       # C5 real engineer posts
│   ├── generated/             # 180 AI-generated outputs
│   └── results/               # Detection, factual, linguistic scores
├── src/ai_text_quality/
│   ├── generate.py            # Prompt building + LLM calls
│   ├── detect.py              # GPTZero + Originality.ai wrappers
│   ├── factcheck.py           # Gold-fact slot matching + LLM judge
│   └── linguistic.py          # 10-feature extraction (spaCy)
└── notebooks/
    ├── 01_task_design.ipynb
    ├── 02_generate.ipynb      # Generate all conditions
    ├── 03_validate.ipynb      # Run all validators
    ├── 04_analysis.ipynb      # Statistics + figures
    └── 05_examples.ipynb      # Side-by-side comparisons
```

### Key Tech Stack
- **Generation:** Claude Sonnet 4 via Anthropic API (temp=0.3, 3 runs/condition)
- **Detection:** GPTZero API + Originality.ai API
- **Linguistic analysis:** spaCy (`en_core_web_sm`)
- **Statistics:** SciPy (Wilcoxon), statsmodels (regression)

### GitHub Repository
**[github.com/yongkyunlee/ai-detectability-research](https://github.com/yongkyunlee/ai-detectability-research)**

---

## Example: C1 vs C3 Side-by-Side

### C1 (Code Only) — GPTZero human_prob: [X.XX]

> In the world of modern AI frameworks, CrewAI stands out as a powerful tool for building multi-agent systems. It is important to note that installation requires Python 3.10 or newer. Furthermore, the framework provides a streamlined setup process. To get started, you can install CrewAI using pip install crewai. Moreover, the project initialization command crewai create crew my_project generates a well-structured template...

**AI tells:** *"In the world of"*, *"It is important to note"*, *"Furthermore"*, *"Moreover"*, uniform sentence length, no contractions

### C3 (Style Constrained) — GPTZero human_prob: [X.XX]

> CrewAI's setup is dead simple — `pip install crewai` and you're off. You'll need Python 3.10+, which shouldn't be an issue for most teams at this point. Run `crewai create crew my_project` and it scaffolds the whole thing: agents.yaml for your agent configs, tasks.yaml for workflows. I've found the YAML-first approach polarizing. It's great for quick iteration, but if you're managing 20+ agents, you'll want to drop into Python classes eventually...

**Improvements:** Contractions, first person, varied sentence length, specific details, opinionated trade-off

---

## Demo & Links

### YouTube Demo
Pre-recorded walkthrough of the generation and evaluation pipeline:

**[YouTube link: placeholder]**

Demo covers:
1. Task definition and gold fact setup
2. Running generation across all 5 conditions
3. Detector API calls and score comparison
4. Linguistic feature extraction
5. Side-by-side output comparison

### References

1. Mitchell et al. (2023). DetectGPT: Zero-Shot Machine-Generated Text Detection
2. Kirchenbauer et al. (2023). A Watermark for Large Language Models
3. Sadasivan et al. (2023). Can AI-Generated Text Be Reliably Detected?
4. Krishna et al. (2024). Paraphrasing Evades Detectors of AI-Generated Text
5. Liang et al. (2023). GPT Detectors Are Biased Against Non-Native English Writers
6. Gao et al. (2023). Enabling LLMs to Generate Text with Citations (ALCE)
7. Liu et al. (2023). Evaluating Verifiability in Generative Search Engines
8. Wang et al. (2025). Humanizing the Machine: Proxy Attacks to Mislead LLM Detectors (ICLR 2025)
9. Wu et al. (2024). DetectRL: Benchmarking LLM-Generated Text Detection in Real-World Scenarios (NeurIPS 2024)
10. Rivera Soto et al. (2025). Language Models Optimized to Fool Detectors Still Have a Distinct Style (NeurIPS 2025 Spotlight)

### GitHub Repository
**[github.com/yongkyunlee/ai-detectability-research](https://github.com/yongkyunlee/ai-detectability-research)**
