# Context Enrichment and Style Intervention for Reducing AI Detectability in Technical Content

**Yongkyun Lee**
Mini Research Project — March 2025

---

## tl;dr

**Problem:** AI-generated technical content is easily detected and dismissed as "AI slop" — 73% of readers say they can spot it, and detection tools report >99% accuracy on raw AI output.

**Method:** 5-condition ablation study across 3 models (Claude Opus 4.6, GPT 5.4, Gemini 3.1) and 3 content lengths, measuring AI detectability and factual accuracy on 22 technical writing tasks.

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
| **Kirchenbauer et al. (2023)** — Watermarking LLMs | Proposes a watermarking framework that embeds detectable green/red token patterns into LLM output during generation |

### Evasion & Robustness

| Paper | Key Contribution |
|---|---|
| **Sadasivan et al. (2023)** — Can AI Text Be Reliably Detected? | Recursive paraphrasing attacks reduce detector accuracy; also demonstrates spoofing attacks and provides theoretical impossibility bounds — motivates our C4 condition |
| **Krishna et al. (2023)** — Paraphrasing Evades Detectors | Builds 11B-param paraphraser (DIPPER) that evades watermarking, GPTZero, DetectGPT; also proposes retrieval-based defense — informs humanization strategy design |
| **Wang et al. (2025)** — Humanizing the Machine (ICLR 2025) | Proxy attack (HUMPA) uses DPO-fine-tuned smaller model to make LLM output evade detectors in both white-box and black-box settings — extends evasion beyond simple paraphrasing |

### Detector Limitations & Evaluation

| Paper | Key Contribution |
|---|---|
| **Liang et al. (2023)** — GPT Detectors Are Biased | Detectors misclassify non-native English writing as AI-generated (61% false positive rate); recommends against deploying detectors in evaluative/educational settings |
| **Wu et al. (2024)** — DetectRL (NeurIPS 2024) | Benchmark showing SOTA detectors underperform in real-world scenarios with adversarial modifications, spelling noise, and human revisions — motivates robust evaluation |
| **Gao et al. (2023)** — ALCE | Citation quality metrics reusable for factual evaluation of generated text |
| **Liu et al. (2023)** — Verifiability in Gen. Search | Surface quality does not equal factual support — motivates measuring both detectability and accuracy |

### Stylistic Features & Interpretability

| Paper | Key Contribution |
|---|---|
| **Rivera Soto et al. (2025)** — Distinct Style Persists (arXiv preprint) | Even models optimized to fool detectors retain identifiable stylistic signatures; stylistic feature space is robust to optimization-based evasion — supports using linguistic features as a robust detection axis (directly relevant to H5) |

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

### Task Set & Experimental Axes
- **22 tasks** across 3 open-source projects (CrewAI, DuckDB, LangChain)
- **3 models via CLI:** Claude Code (Opus 4.6), Codex CLI (GPT 5.4), Gemini CLI (3.1)
- **3 content lengths:** Short (150–250), Medium (300–500), Long (700–1000 words)
- **3 runs per condition** → ~750 documents total

| Sub-experiment | Models | Lengths | Conditions | Texts |
|---|---|---|---|---|
| Core ablation | Claude Code | Medium | C1–C4 | 264 |
| Model comparison | All 3 CLIs | Medium | C1, C3 | 396 |
| Length variation | Claude Code | All 3 | C1, C3 | 396 |

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

### Axis 2: Factual Accuracy (Claim-Based Verification)

| Step | How It Works |
|---|---|
| **1. Claim extraction** | LLM extracts atomic factual claims from generated text |
| **2. Claim verification** | Separate LLM checks each claim against reference docs → CORRECT / INCORRECT / UNVERIFIABLE |
| **Factual precision** (primary) | `correct / (correct + incorrect)` — measures correctness, not coverage |

**Why not gold fact tables?** Gold facts from docs may not be what a blog post naturally covers. This avoids penalizing natural writing that omits some details.

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

### Statistical Tests (Paired Wilcoxon, n=22 tasks)

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
| Factual precision | [X.XX] | [X.XX] | [X.XX] | [X.XX] | — |
| Style distance from human | [X.XX] | [X.XX] | [X.XX] | [X.XX] | 0.00 |

- **H3 result:** C4 achieves [lowest/near-lowest] detectability but factual precision drops by [X]% — humanization introduces paraphrasing errors
- **H4 result:** C3 closes **[W]%** of the C1→C5 gap on detector scores with only **[V]%** factual precision loss
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

## Results: Model Comparison

### AI Detectability by Model (C1 Baseline)

```
           Mean human_prob (higher = less detectable)
           ┌──────────────────────────────────────────────────┐
Claude     │████████████░░░░░░░░░░░░░░░░░░░░░░░░░░│ [0.XX]
GPT 5.4    │██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ [0.XX]
Gemini 3.1 │████████████████░░░░░░░░░░░░░░░░░░░░░░│ [0.XX]
           └──────────────────────────────────────────────────┘
```

### With Style Constraints (C3)

```
           Mean human_prob (higher = less detectable)
           ┌──────────────────────────────────────────────────┐
Claude     │████████████████████░░░░░░░░░░░░░░░░░░│ [0.XX]
GPT 5.4    │██████████████████░░░░░░░░░░░░░░░░░░░░│ [0.XX]
Gemini 3.1 │██████████████████████░░░░░░░░░░░░░░░░│ [0.XX]
           └──────────────────────────────────────────────────┘
```

### Key Finding (H6)
- [TBD: Which model is most/least detectable by default?]
- [TBD: Do style constraints help equally across all models?]

---

## Results: Content Length vs. AI Detectability

### Detectability by Content Length (C1 Baseline)

```
           Mean human_prob (higher = less detectable)
           ┌──────────────────────────────────────────────────┐
Short      │████████████████████░░░░░░░░░░░░░░░░░░│ [0.XX]
Medium     │████████████░░░░░░░░░░░░░░░░░░░░░░░░░░│ [0.XX]
Long       │████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ [0.XX]
           └──────────────────────────────────────────────────┘
```

### Key Finding (H7)
- [TBD: Does longer content expose more AI patterns?]
- [TBD: Is there a "sweet spot" length for evading detection?]
- [TBD: Correlation between word count and detectability score]

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
│   ├── tasks/                 # 15 task definitions + reference docs
│   ├── context/               # Rich context per project
│   ├── human_baselines/       # C5 real engineer posts
│   ├── generated/             # 180 AI-generated outputs
│   └── results/               # Detection, factual, linguistic scores
├── src/ai_text_quality/
│   ├── generate.py            # Prompt building + LLM calls
│   ├── detect.py              # GPTZero + Originality.ai wrappers
│   ├── factcheck.py           # Claim extraction + verification
│   └── linguistic.py          # 10-feature extraction (spaCy)
└── notebooks/
    ├── 01_task_design.ipynb
    ├── 02_generate.ipynb      # Generate all conditions
    ├── 03_validate.ipynb      # Run all validators
    ├── 04_analysis.ipynb      # Statistics + figures
    └── 05_examples.ipynb      # Side-by-side comparisons
```

### Key Tech Stack
- **Generation:** Claude Code + Codex CLI + Gemini CLI (3 runs/condition, no API keys)
- **Fact checking:** Claim extraction + verification via LLM-as-judge (cross-model)
- **Detection:** GPTZero + Originality.ai
- **Linguistic analysis:** spaCy (`en_core_web_sm`)
- **Statistics:** SciPy (Wilcoxon, Kruskal-Wallis), statsmodels (regression)

### GitHub Repository (Code)
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
1. Task definition and reference doc setup
2. Running generation across conditions, models, and lengths
3. Claim extraction and fact-checking pipeline
4. Detector score comparison (GPTZero + Originality.ai)
5. Model comparison and length variation analysis
6. Side-by-side output comparison

### References

1. Mitchell et al. (2023). DetectGPT: Zero-Shot Machine-Generated Text Detection
2. Kirchenbauer et al. (2023). A Watermark for Large Language Models
3. Sadasivan et al. (2023). Can AI-Generated Text Be Reliably Detected?
4. Krishna et al. (2023). Paraphrasing Evades Detectors of AI-Generated Text, but Retrieval Is an Effective Defense (NeurIPS 2023)
5. Liang et al. (2023). GPT Detectors Are Biased Against Non-Native English Writers
6. Gao et al. (2023). Enabling LLMs to Generate Text with Citations (ALCE)
7. Liu et al. (2023). Evaluating Verifiability in Generative Search Engines
8. Wang et al. (2025). Humanizing the Machine: Proxy Attacks to Mislead LLM Detectors (ICLR 2025)
9. Wu et al. (2024). DetectRL: Benchmarking LLM-Generated Text Detection in Real-World Scenarios (NeurIPS 2024)
10. Rivera Soto et al. (2025). Language Models Optimized to Fool Detectors Still Have a Distinct Style (and How to Change It) (arXiv preprint)

### GitHub Repository (Slides)
**[github.com/yongkyunlee/ai-detectability-research](https://github.com/yongkyunlee/ai-detectability-research)**

---

## Appendix: Detailed Paper Summaries

---

### Paper 1: DetectGPT — Mitchell et al. (2023)

**Full Title:** DetectGPT: Zero-Shot Machine-Generated Text Detection using Probability Curvature

**Authors:** Eric Mitchell, Yoonho Lee, Alexander Khazatsky, Christopher D. Manning, Chelsea Finn (Stanford University)

**Venue:** ICML 2023

**Core Idea:**
- AI-generated text tends to occupy **negative curvature regions** of the source model's log probability function
- Human text does not exhibit this property — minor perturbations of human text can increase or decrease log probability equally

**Method:**
1. Given a candidate passage, generate ~100 perturbations using a generic LM (T5)
2. Compute log probability of the original passage and each perturbation under the source model
3. If the original has significantly higher log probability than perturbations (negative curvature), classify as machine-generated

**Key Results:**
- Improves fake news detection (GPT-NeoX 20B) from 0.81 AUROC (best zero-shot baseline) to **0.95 AUROC**
- Zero-shot: no training data, no classifier, no watermarking required
- Requires white-box access to the source model's log probabilities

**Limitations:**
- Needs access to the source model (or a similar model) for log probability computation
- Computationally expensive (~100 forward passes per document)
- Performance degrades when source model is unknown

**Relevance to This Study:** DetectGPT is a foundational method — GPTZero and similar commercial tools build on its principles. Understanding its log-probability basis explains why stylistic interventions can shift detector scores.

---

### Paper 2: A Watermark for Large Language Models — Kirchenbauer et al. (2023)

**Full Title:** A Watermark for Large Language Models

**Authors:** John Kirchenbauer, Jonas Geiping, Yuxin Wen, Jonathan Katz, Ian Miers, Tom Goldstein (University of Maryland)

**Venue:** ICML 2023

**Core Idea:**
- Embed an imperceptible statistical signal into LLM output at generation time by manipulating token sampling

**Method:**
1. Before generating each token, hash the previous token to seed a random number generator
2. Use the seed to partition the vocabulary into a **"green list"** and a **"red list"**
3. During sampling, softly promote green list tokens (add a bias delta to their logits)
4. Detection: count green list tokens — a z-test determines if the count exceeds what's expected by chance

**Key Results:**
- Detectable from as few as **25 tokens** with negligible impact on text quality
- Detection is efficient and does not require access to the model itself — only the hash function
- p-values as low as ~6x10^-14 for watermarked text
- Robustness: significant token modifications needed to remove the watermark

**Limitations:**
- Low-entropy sequences (e.g., code, formulaic text) are hard to watermark without quality degradation
- Requires cooperation from the model provider to embed the watermark
- Vulnerable to paraphrasing attacks (as shown by Krishna et al. and Sadasivan et al.)

**Relevance to This Study:** Demonstrates that token distribution patterns are a primary axis for detection. Our C3 style constraints work in a complementary space — modifying stylistic patterns rather than token-level statistics.

---

### Paper 3: Can AI-Generated Text Be Reliably Detected? — Sadasivan et al. (2023)

**Full Title:** Can AI-Generated Text be Reliably Detected?

**Authors:** Vinu Sankar Sadasivan, Aounon Kumar, Sriram Balasubramanian, Wenxiao Wang, Soheil Feizi (University of Maryland)

**Venue:** arXiv preprint (2023)

**Core Idea:**
- Stress-tests AI text detectors with **recursive paraphrasing attacks** and **spoofing attacks**, revealing fundamental vulnerabilities

**Method — Evasion (Recursive Paraphrasing):**
- Repeatedly paraphrase AI-generated text using an external paraphrasing model
- Each round further removes detectable statistical signatures

**Key Results — Evasion:**
- Watermarking detection (TPR@1%FPR) drops from **99.3% to 9.7%** after recursive paraphrasing
- DetectGPT AUROC drops from **96.5% to 25.2%**
- RoBERTa-Large-Detector TPR@1%FPR drops from **100% to 60%**
- Human evaluation: 77% of paraphrased passages rated high quality for content preservation; 89% for grammar

**Method — Spoofing:**
- An adversary queries the watermarked LLM multiple times to **infer the watermarking scheme**
- Can then compose human-written text that triggers watermark detection (false positives)

**Theoretical Framework:**
- Links AUROC of the best possible detector to **Total Variation (TV) distance** between human and AI text distributions
- As LLMs improve and TV distance shrinks, reliable detection becomes fundamentally harder

**Relevance to This Study:** Directly motivates C4 (humanization) — paraphrasing is a powerful evasion tool but introduces quality trade-offs. The theoretical bounds contextualize why evasion is possible.

---

### Paper 4: Paraphrasing Evades Detectors — Krishna et al. (2023)

**Full Title:** Paraphrasing Evades Detectors of AI-Generated Text, but Retrieval Is an Effective Defense

**Authors:** Kalpesh Krishna, Yixiao Song, Marzena Karpinska, John Wieting, Mohit Iyyer (UMass Amherst, Google, Google DeepMind)

**Venue:** NeurIPS 2023

**Core Idea:**
- Builds **DIPPER**, an 11B-parameter discourse-level paraphraser with controllable diversity, to attack AI text detectors
- Proposes a **retrieval-based defense** robust to paraphrasing

**DIPPER Paraphraser:**
- Trained to paraphrase paragraph-length text (not just sentences)
- Two control knobs: **lexical diversity** and **content reordering**
- Can condition on surrounding context (e.g., user prompts)

**Attack Results:**
- DetectGPT detection drops from **70.3% to 4.6%** (at 1% FPR) after DIPPER paraphrasing
- Effective against watermarking, GPTZero, DetectGPT, and OpenAI's text classifier
- Works across multiple LLMs including GPT-3.5-davinci-003

**Retrieval-Based Defense:**
- LLM API provider stores all generated outputs in a database
- Given candidate text, search for semantically similar matches using BM-25 and semantic embeddings
- Detects **80-97%** of paraphrased generations at 1% FPR (tested on 15M generation database)
- Robust to paraphrasing because it relies on semantics, not statistical surface patterns

**Relevance to This Study:** DIPPER's controllable paraphrasing directly informs our C4 humanization strategy. The retrieval defense shows that evasion has limits when API providers participate.

---

### Paper 5: GPT Detectors Are Biased — Liang et al. (2023)

**Full Title:** GPT Detectors Are Biased Against Non-Native English Writers

**Authors:** Weixin Liang, Mert Yuksekgonul, Yining Mao, Eric Wu, James Zou (Stanford University)

**Venue:** Patterns (Cell Press), 2023

**Core Idea:**
- GPT detectors systematically misclassify non-native English writing as AI-generated due to lower linguistic variability

**Key Experiments:**
- Tested 7 detectors (GPTZero, Originality.AI, ZeroGPT, etc.) on 91 TOEFL essays + 88 US 8th-grade essays
- Non-native TOEFL essays: **61.22% average false positive rate** (misclassified as AI)
- Native US essays: **near-zero** false positive rate
- 18/91 TOEFL essays (19.78%) were **unanimously** flagged as AI by all 7 detectors

**Mechanism:**
- Non-native writing has lower perplexity due to reduced lexical richness, syntactic complexity, and vocabulary diversity
- Detectors rely heavily on perplexity — low perplexity = flagged as AI

**Mitigation:**
- Prompting ChatGPT to "enhance word choices to sound more native" reduced false positives from **61.22% to 11.77%**
- Reverse: simplifying native essays to "sound non-native" increased false positives from **5.19% to 56.65%**

**Detector Bypass:**
- Self-edit prompts ("Elevate text by employing literary language") reduced detection of AI-generated college essays from **100% to 13%**

**Relevance to This Study:** Motivates awareness of fairness when interpreting detector scores. Also demonstrates that simple rewriting prompts can dramatically shift detection — a finding that validates our C4 approach.

---

### Paper 6: ALCE — Gao et al. (2023)

**Full Title:** Enabling Large Language Models to Generate Text with Citations

**Authors:** Tianyu Gao, Howard Yen, Jiatong Yu, Danqi Chen (Princeton University)

**Venue:** EMNLP 2023

**Core Idea:**
- First reproducible benchmark for evaluating LLM-generated text with citations, measuring fluency, correctness, and citation quality

**Benchmark Design:**
- Three datasets: ASQA (ambiguous factoid), QAMPARI (list factoid), ELI5 (why/how/what)
- Corpora: Wikipedia (21M passages) and Sphere (899M passages)
- End-to-end evaluation: retrieve evidence, generate answer, cite passages

**Evaluation Metrics:**
- **Fluency:** MAUVE score
- **Correctness:** Dataset-specific metrics (exact match, F1)
- **Citation quality:** NLI-based — checks if cited passage actually supports the statement (citation precision and recall)

**Key Findings:**
- Even the best models (ChatGPT, GPT-4) lack complete citation support **~50% of the time** on ELI5
- Closed-book models achieve good correctness but poor citation quality
- More retrieved passages help GPT-4 but not ChatGPT
- Reranking multiple generations improves citation quality

**Relevance to This Study:** ALCE's citation quality metrics (NLI-based verification) inform our factual accuracy evaluation — we adapt the principle of checking whether generated claims are supported by source material.

---

### Paper 7: Evaluating Verifiability in Generative Search Engines — Liu et al. (2023)

**Full Title:** Evaluating Verifiability in Generative Search Engines

**Authors:** Nelson F. Liu, Tianyi Zhang, Percy Liang (Stanford University)

**Venue:** EMNLP 2023 (Findings)

**Core Idea:**
- Audits four generative search engines (Bing Chat, NeevaAI, perplexity.ai, YouChat) for **verifiability** — whether cited sources actually support generated claims

**Key Metrics:**
- **Citation recall:** % of statements fully supported by citations
- **Citation precision:** % of citations that support their associated statement

**Key Findings:**
- Responses appear fluent and informative but are frequently unsupported
- Only **51.5%** of generated sentences are fully supported by citations (on average)
- Only **74.5%** of citations actually support their associated statement
- Systems vary: Bing Chat has the highest citation precision; perplexity.ai has the highest recall

**Core Insight:**
- **Surface quality does not equal factual support** — fluent, confident text can be deeply unreliable
- This "facade of trustworthiness" is particularly dangerous for information-seeking users

**Relevance to This Study:** Directly motivates our dual-metric approach: measuring both detectability (surface quality) and factual accuracy. A generated text that evades detectors but introduces errors is not a useful outcome.

---

### Paper 8: Humanizing the Machine (HUMPA) — Wang et al. (2025)

**Full Title:** Humanizing the Machine: Proxy Attacks to Mislead LLM Detectors

**Authors:** Tianchun Wang, Yuanzhou Chen, Zichuan Liu, Zhanwen Chen, Haifeng Chen, Xiang Zhang, Wei Cheng (Penn State, UCLA, Nanjing University, UVA, NEC Labs)

**Venue:** ICLR 2025

**Core Idea:**
- A **proxy attack** (HUMPA) that uses a small, RL-fine-tuned "humanized" language model to shift a large source model's output distribution toward human-like text during decoding

**Method:**
1. Fine-tune a small LM (e.g., Llama3-8B) using **DPO** with preference data from detector scores (human-like = preferred)
2. At inference, the humanized SLM modifies the large source model's token probabilities during decoding
3. No fine-tuning of the source model required — the attack is a decoding-time intervention

**Key Results:**
- Average AUROC drop of **70.4%** across multiple datasets
- Maximum AUROC drop of **95.0%** on a single dataset
- Cross-discipline scenarios: up to **90.9%** relative decrease in detection accuracy
- Cross-language scenarios: up to **91.3%** relative decrease
- Generation quality remains preserved within a modest utility budget

**Tested Models:** Llama2-13B, Llama3-70B, Mixtral-8x7B (white-box and black-box settings)

**Theoretical Contribution:**
- Proves that attacking with a proxy humanized SLM is theoretically comparable to directly fine-tuning the large source model

**Relevance to This Study:** Extends evasion beyond post-hoc paraphrasing to generation-time intervention. Our C4 condition tests a simpler version of this principle (rewriting), while HUMPA shows even stronger results are achievable at the model level.

---

### Paper 9: DetectRL — Wu et al. (2024)

**Full Title:** DetectRL: Benchmarking LLM-Generated Text Detection in Real-World Scenarios

**Authors:** Junchao Wu, Runzhe Zhan, Derek F. Wong, Shu Yang, Xinyi Yang, Yulin Yuan, Lidia S. Chao (University of Macau)

**Venue:** NeurIPS 2024 (Datasets and Benchmarks Track)

**Core Idea:**
- A benchmark showing that SOTA detectors **underperform significantly** in real-world conditions vs. idealized lab settings

**What Makes It "Real-World":**
- **Various prompt usages:** Different instruction styles that users actually employ
- **Human revisions:** Word substitutions simulating human editing of AI text
- **Writing noise:** Spelling mistakes, typos, informal language
- **Adversarial perturbations:** Prompt-based attacks, paraphrasing, data mixing
- **Domain diversity:** Academic writing, news, creative writing, social media

**LLMs Tested:** GPT-3.5-turbo, PaLM-2-bison, Claude-instant, Llama-2-70b

**Key Findings:**
- Adversarial perturbation attacks reduce **all zero-shot detectors** by an average of **39.28% AUROC**
- Informal domain data (social media) degrades detection most
- Shorter training data builds more robust detectors; longer test data improves detection
- Supervised detectors are more robust than zero-shot methods across attack types
- When human-written text undergoes attacks, detector performance is minimally affected (or even improves)

**Relevance to This Study:** Validates our multi-detector evaluation approach and the importance of testing under realistic conditions (not just clean AI output vs. clean human text).

---

### Paper 10: Distinct Style Persists — Rivera Soto et al. (2025)

**Full Title:** Language Models Optimized to Fool Detectors Still Have a Distinct Style (and How to Change It)

**Authors:** Rafael Rivera Soto, Barry Chen, Nicholas Andrews (Lawrence Livermore National Lab, Johns Hopkins University)

**Venue:** arXiv preprint (2025)

**Core Idea:**
- Even when LLMs are explicitly optimized (via RL) to evade detectors, they retain **identifiable stylistic signatures** in a stylistic feature space

**Key Findings:**

*Stylistic robustness:*
- Models fine-tuned to fool traditional detectors (log-probability based) still have a **distinct writing style** detectable in stylistic feature space
- Even when models are explicitly optimized *against* stylistic detectors, detection performance remains **surprisingly unaffected**

*New attack — style-aware paraphrasing:*
- Proposes a paraphrasing approach that simultaneously closes the stylistic gap and evades traditional detectors
- For **single-sample detection**, this attack is universally effective across all detectors
- However, as the **number of samples grows**, human and machine distributions become distinguishable again

*Multi-sample detection:*
- With sufficient samples from the same source, stylistic analysis can reliably distinguish human from machine text regardless of optimization

**Core Insight:**
- Single-document detection is fundamentally fragile, but **multi-document stylistic analysis** provides a robust detection axis

**Relevance to This Study:** Directly supports our H5 hypothesis — measurable linguistic features (sentence variance, contractions, discourse markers) form a robust detection axis. Our 10-feature linguistic analysis aligns with this paper's findings that style persists even under adversarial conditions.
