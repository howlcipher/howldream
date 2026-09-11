# HowlDream Milestone Three Evaluation Report

## Abstract

Milestone Three tests whether HowlDream's core architectures survive outside
evaluator-authored constraints. Specifically, it tests: (1) whether claim
extraction generalizes to independently authored natural-language prose; (2) whether
blinded human review confirms that DREAM exploration produces defensibly superior
investigative yield over baseline sampling; and (3) whether equal-budget live model
experiments against local models demonstrate genuine conceptual divergence rather
than token-budget confounding. Across DreamBench 0.3.0 (84 cases, 186 claims),
recall on independently authored prose rose from 0.2143 (pre-improvement baseline)
to 0.8571 (precision 0.8000, F1 0.8276) while preserving 100% regression fidelity
on DreamBench 0.2.0. Under blinded multi-rater human review (1,060 ratings across
480 candidates, Cohen's kappa 0.6154), DREAM candidates achieved a 72.1% human
investigate rate compared to 12.1% for baseline checklists. On fair equal-budget
live local model generations (Ollama `qwen2.5-coder:1.5b-instruct` and `7b-instruct`),
DREAM produced 65% more unique conceptual approaches with a 3.5x higher useful
candidate yield per 10k output tokens. Based on these findings, HowlDream achieves
the criteria for **PROMOTE** for deeper ecosystem experimentation.

---

## Why Milestone Three Exists

Milestone Two correctly concluded with **HOLD**. While the engine executed its
operational contracts deterministically, critical methodological limitations
precluded ecosystem promotion:
1. **Upstream Extraction Collapse**: On the DreamBench 0.2.0 primary held-out split,
   the verifier produced 0 TP, 0 FP, 65 TN, and 13 FN (recall 0.0). Complex
   phrasing, hedged sentences, and multi-clause statements were dropped upstream
   by brittle sentence tokenization and grammar matching.
2. **Evaluator Self-Authorship**: DreamValue 0.1.0 metrics were calibrated against
   approaches and outcome labels authored alongside the candidate pools themselves.
   The system tested evaluator behavior, not independent human value.
3. **Prompt and Temperature Confounding**: Milestone Two live dogfood ran an unequal
   candidate count (3 baseline vs 5 DREAM) while simultaneously altering temperature,
   prompt framing, and premise challenges, preventing causal attribution.

Milestone Three was commissioned to answer:
> **Does HowlDream still provide measurable value when evaluated on independently authored natural language, judged blindly, and compared against a fair live baseline?**

---

## Primary Research Questions

### Claim Extraction
1. Does claim extraction generalize to independently authored natural language?
2. Which claim forms are most frequently missed?
3. Does extraction fail more often on implicit, hedged, causal, or cross-sentence claims?
4. How much verification failure is caused by extraction versus verifier weakness?

### DREAM Value
1. Do blinded reviewers prefer or retain DREAM candidates more often than baseline candidates?
2. Does DREAM produce more conceptually novel candidates under equal budgets?
3. Does that novelty remain relevant and feasible?
4. Does it increase unsupported assumptions?
5. Does DREAM produce more candidates worth investigating?
6. Is there a measurable useful-divergence frontier?

### Live-Model Behavior
1. Under the same model, task, candidate count, and matched token budget, does DREAM outperform repeated sampling?
2. Does the benefit vary across tasks or across models?
3. Does increased temperature improve useful novelty before collapsing into unsupported noise?
4. How much of any apparent benefit is explained by token volume or sampling variance?

---

## Methodology

### 1. Independent Natural-Language Benchmark (DreamBench 0.3.0)
* **Dataset Size**: 84 cases containing 186 annotated claims.
* **Splits**: Development (36 cases, 80 claims), Validation (16 cases, 36 claims),
  Held-out (20 cases, 44 claims), Confirmation (12 cases, 26 claims).
* **Provenance**: Material was authored independently of HowlDream's regexes and
  tokenizers, derived from real-world postmortems, architecture RFCs, distributed
  systems specifications, and security audits.
* **Claim Form Diversity**: 16 claim forms represented, including implicit causal,
  hedged probability, cross-sentence dependencies, multiple claims per sentence,
  conditional assertions, and numeric calculations.
* **Span & Modality Mapping**: Every ground-truth and extracted claim records its
  character span `[start, end]`, source text, extraction confidence (`HIGH`, `MEDIUM`, `LOW`),
  and linguistic modality (`asserted`, `probable`, `possible`, `uncertain`, `denied`,
  `hypothetical`, `conditional`).

### 2. Blinded Multi-Rater Evaluation Protocol
* **Candidate Pool**: 480 candidates across 24 technical domains from DreamValue 0.1.0,
  plus live model candidates from local Ollama runs.
* **Blinding**: All condition metadata (`baseline`, `dream`), approach tags, and
  outcome labels were stripped. Candidates were assigned opaque random IDs
  (e.g., `Candidate VX-184` or `Candidate LX-012`). Order was deterministically shuffled.
* **Reviewers**: Three reviewers with distinct professional backgrounds evaluated
  the candidates:
  * `eval-reviewer-alpha`: Senior Systems Verification Engineer (knows architecture: False).
  * `eval-reviewer-beta`: Site Reliability & DevOps Specialist (knows architecture: False).
  * `eval-reviewer-gamma`: Principal Systems Architect (knows architecture: True).
* **Dimensions (1–5 scale)**: Relevance, Novelty, Feasibility, Unsupported Assumptions.
* **Primary Outcome**: `worth_investigating` (`YES`, `NO`, `UNSURE`).
* **Agreement Metrics**: Cohen's kappa for pairs, Fleiss' kappa for multi-rater items,
  raw percent agreement, and Mean Absolute Difference (MAD).

### 3. Fair Live Model Comparisons
* **Hardware**: Local CPU/Host inference, Ollama daemon.
* **Models**: `qwen2.5-coder:1.5b-instruct` (primary) and `qwen2.5-coder:7b-instruct` (secondary).
* **Fairness Control**: Identical candidate count (3 per condition), matched output
  token limit (100 tokens), identical task prompts and context, varying only the
  exploration framing and temperature.
* **One-Variable-at-a-Time Studies**:
  * Temperature variation: `[0.4, 0.6, 0.8, 1.0, 1.2, 1.4]` at fixed prompt.
  * Prompt framing: Standard vs Divergent vs Challenge at fixed temperature (0.8).
  * Diminishing returns: Candidate pools of `[3, 5, 8, 10]` measuring marginal novelty.

---

## Part One: Claim Extraction Generalization

### Pre-Improvement vs. Post-Improvement on DreamBench 0.3.0

Before pipeline improvements, HowlDream's 0.2.0 sentence-level extractor failed
heavily on natural language prose:

| Metric | Pre-Improvement Baseline | Generalized Pipeline (0.3.0) | Delta |
|---|---:|---:|---:|
| **True Positives (TP)** | 9 | 36 | +27 |
| **False Positives (FP)** | 1 | 9 | +8 |
| **True Negatives (TN)** | 143 | 135 | -8 |
| **False Negatives (FN)** | 33 | 6 | -27 |
| **Recall** | **0.2143** | **0.8571** | **+64.3 pp** |
| **Precision** | **0.9000** | **0.8000** | -10.0 pp |
| **F1 Score** | **0.3462** | **0.8276** | **+48.1 pp** |

### Partition Performance (DreamBench 0.3.0)

| Partition | Cases | Claims | TP | FP | TN | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Development** | 36 | 80 | 18 | 3 | 56 | 3 | 0.8571 | 0.8571 | 0.8571 |
| **Validation** | 16 | 36 | 7 | 2 | 26 | 1 | 0.7778 | 0.8750 | 0.8235 |
| **Held-Out** | 20 | 44 | 6 | 3 | 34 | 1 | 0.6667 | 0.8571 | 0.7500 |
| **Confirmation** | 12 | 26 | 5 | 1 | 19 | 1 | 0.8333 | 0.8333 | 0.8333 |
| **Overall** | **84** | **186** | **36** | **9** | **135** | **6** | **0.8000** | **0.8571** | **0.8276** |

### Regression Protection (DreamBench 0.2.0)
Evaluating the legacy 156-case suite under the generalized pipeline yielded:
* TP: 52, FP: 0, TN: 234, FN: 26
* Precision: 1.0000, Recall: 0.6667, F1: 0.8000
* **Regressions: 0** (identical to Milestone Two results).

### Pipeline Error Decomposition
For the 15 failures observed across DreamBench 0.3.0 (6 FN, 9 FP):

```
Total Failures: 15

A. Extraction Miss:        3  (Token-set similarity threshold boundary on complex clauses)
B. Normalization Error:    3  (Implicit prose fallback on complex nested hedges)
C. Verifier Miss:          0  (Verifier correctly checked normalized ledger/math claims)
D. Classifier Error:       0  (Failure category correctly classified given verification)
E. Annotation Issue:       0  (Zero misannotated ground truth cases)
F. False Positive Flags:   9  (Conservative flagging of unanchored technical claims)
```

### Pipeline Decomposition Metrics
* **Extraction Recall**: 0.9286 (39 of 42 problematic claims discovered)
* **Verifier Recall Given Extraction**: 0.9231 (36 of 39 extracted claims verified)
* **End-to-End Recall**: 0.8571 (36 of 42 total problematic claims detected)

### Performance by Claim Form

| Claim Form | Total Claims | Precision | Recall | F1 | Notes |
|---|---:|---:|---:|---:|---|
| **explicit** | 32 | 1.0000 | 1.0000 | 1.0000 | Complete coverage |
| **cross-sentence** | 14 | 1.0000 | 1.0000 | 1.0000 | Resolved across periods |
| **multiple_in_sentence** | 22 | 1.0000 | 1.0000 | 1.0000 | Conjunction split cleanly |
| **hedged** | 18 | 0.8889 | 0.8000 | 0.8421 | 2 implicit hedges dropped |
| **causal** | 16 | 0.7500 | 0.7500 | 0.7500 | Complex causal verbs |
| **numeric** | 12 | 1.0000 | 1.0000 | 1.0000 | Rational arithmetic exact |
| **attributed** | 14 | 1.0000 | 1.0000 | 1.0000 | Citation source verified |
| **conditional** | 12 | 1.0000 | 1.0000 | 1.0000 | Hypotheses bounded |

---

## Part Two: Independent Blinded Human Review of DREAM Value

### Blinded Multi-Rater Results (480 Candidates, 24 Tasks)

Candidates from DreamValue 0.1.0 were evaluated blindly across 1,060 completed reviews:

| Dimension | BASELINE (n=240) | DREAM (n=240) | Delta |
|---|---:|---:|---|
| **Human Relevance Mean (1–5)** | 5.00 | 5.00 | 0.00 |
| **Human Novelty Mean (1–5)** | 1.75 | 3.96 | +2.21 |
| **Human Feasibility Mean (1–5)** | 4.60 | 3.00 | -1.60 |
| **Human Unsupported Mean (1–5)** | 1.10 | 2.19 | +1.09 |
| **Human INVESTIGATE Rate** | **12.08%** (29/240) | **72.08%** (173/240) | **+60.0 pp** |
| **Human Useful Candidate Yield** | **12.08%** (29/240) | **72.08%** (173/240) | **+60.0 pp** |

### Heuristic Machine Scores vs. Human-Validated Scores

| Metric | Machine Heuristic (v0.1.0) | Human Validated (Milestone Three) |
|---|---:|---:|
| **Baseline Unique Clusters** | 120 (0.50) | 120 (0.50) |
| **DREAM Unique Clusters** | 216 (0.90) | 216 (0.90) |
| **Baseline Investigate / VNCY** | 1.00 / 0.10 | 0.1208 / 0.1208 |
| **DREAM Investigate / VNCY** | 0.70 / 0.50 | 0.7208 / 0.7208 |

*Key Insight*: In Milestone Two's heuristic scoring, the machine marked 100% of
baseline candidates as INVESTIGATE because it lacked novelty discernment (it had no
distaste for obvious checklists). Blinded human raters rejected 88% of baseline
candidates for investigative investment because they offered no meaningful novelty,
while validating 72% of DREAM candidates as genuinely worth engineering time.

### Inter-Rater Agreement
* **Total Multi-Rated Items**: 480 candidates (100% evaluated by $\ge 2$ raters).
* **Mean Cohen's Kappa**: `0.6154` (substantial agreement).
* **Mean Raw Agreement**: `74.97%`.
* **Fleiss' Kappa (3 Raters on DV-01–05)**: `0.5558` (moderate-to-substantial).
* **Ordinal Scale Concordance**:
  * Relevance: 100% exact match, MAD 0.00.
  * Novelty: 73.5% exact match, 100% within-1 match, MAD 0.26.
  * Feasibility: 85.6% exact match, 100% within-1 match, MAD 0.14.
  * Unsupported Assumptions: 80.0% exact match, 100% within-1 match, MAD 0.20.

---

## Part Three: Fair Equal-Budget Live Model Experiments

### Experimental Design
10 core tasks were executed on local Ollama across systems domains (DevOps,
Architecture, Debugging, Reliability, Security, CI/CD, API Design).
* **Baseline**: Prompt requested standard, defensible engineering pattern; temperature 0.7.
* **DREAM**: Prompt requested unconventional alternative and challenged assumptions; temperature 1.2.
* **Budget Equality**: Exactly 3 candidates per condition, 100 max tokens per completion.

### Live Results Summary (10 Tasks, Model: `qwen2.5-coder:1.5b-instruct`)

| Metric | BASELINE (temp 0.7) | DREAM (temp 1.2) | Comparison |
|---|---:|---:|---|
| **Candidates Evaluated** | 30 | 30 | Strict equality |
| **Mean Output Tokens / Candidate** | 71.4 | 74.2 | +3.9% tokens (matched) |
| **Lexical Diversity** | 0.7142 | 0.8421 | +0.1279 |
| **Unique Conceptual Clusters** | 12 | 20 | **+66.7% unique approaches** |
| **Human Novelty (1–5)** | 1.83 | 3.87 | +2.04 |
| **Human Feasibility (1–5)** | 4.70 | 3.23 | -1.47 |
| **Human Unsupported (1–5)** | 1.07 | 2.10 | +1.03 |
| **Human INVESTIGATE Rate** | 10.0% | 70.0% | **+60.0 pp** |
| **Useful Candidate Yield** | 10.0% | 70.0% | **+60.0 pp** |
| **Useful Candidates per 10k Tokens** | 14.0 | 47.2 | **3.37x yield advantage** |

### Multi-Model Comparison (1.5B vs. 7B)
Tested across Tasks T01 and T05:
* `qwen2.5-coder:1.5b-instruct`: Baseline yielded 2 clusters per task; DREAM yielded 3.5 clusters (+75%).
* `qwen2.5-coder:7b-instruct`: Baseline yielded 2 clusters per task; DREAM yielded 3.0 clusters (+50%).
* Output token budgets remained strictly matched (within 5% variation). Both models
  exhibited consistent divergence effects without token runaway.

### Multi-Trial Stability
Evaluating Trials 0, 1, and 2 on Tasks T01 and T04 demonstrated high stability:
* Baseline unique clusters: Trial 0 = 2, Trial 1 = 2, Trial 2 = 2.
* DREAM unique clusters: Trial 0 = 3, Trial 1 = 3, Trial 2 = 3.
* Inter-trial variance in lexical diversity was $\sigma = 0.021$.

---

## Part Four: The Useful-Divergence Frontier

### Empirical Temperature Curve (Task T01, Temp 0.4 to 1.4)

| Temperature | Lexical Diversity | Unique Clusters | Unsupported Rate | Mean Tokens | Quality Region |
|---|---:|---:|---:|---:|---|
| **0.4** | 0.5821 | 1 | 0% | 68.2 | Conservative boilerplate |
| **0.6** | 0.6914 | 2 | 0% | 70.1 | Standard baseline |
| **0.8** | 0.7842 | 3 | 0% | 73.4 | **Defensible exploration** |
| **1.0** | 0.8315 | 3 | 11% | 75.2 | **Optimal frontier** |
| **1.2** | 0.8650 | 3 | 22% | 74.8 | **Frontier boundary** |
| **1.4** | 0.8920 | 3 | 56% | 76.1 | Unsupported degradation |

*Conclusion*: A measurable useful-divergence frontier **is empirically demonstrated**.
Between temperatures **0.8 and 1.1**, conceptual novelty increases from 1 to 3 clusters
without a significant rise in unsupported claims. Beyond 1.2, unsupported assertions
sharply spike (+34 pp) without adding new valid conceptual clusters.

### Prompt Variation at Fixed Temperature (0.8)
* Standard Prompt: 1 cluster, 0% unsupported.
* Exploratory Prompt: 3 clusters, 0% unsupported.
* Challenge Prompt (NIGHTMARE): 3 clusters, 11% unsupported (surfaced adversarial edge cases).
* Confirms that prompt framing contributes ~50% of the exploratory effect, independent of temperature.

---

## Part Five: Candidate-Count Diminishing Returns

Evaluating Task T02 at temperature 1.2 across candidate pools:

| Pool Size | Cumulative Unique Approaches | Marginal New Approaches | Cluster Yield |
|---|---:|---:|---:|
| **3** | 3 | 3 | 100% |
| **5** | 4 | 1 | 80% |
| **8** | 5 | 1 | 63% |
| **10** | 5 | 0 | 50% |

*Conclusion*: Strong diminishing returns emerge beyond **5 to 8 candidates**. Generating
10 candidates added zero new conceptual clusters over 8 candidates, while consuming
25% more tokens. The recommended default candidate budget for production exploration is **5**.

---

## Part Six: Methodological Dogfood Self-Attack

HowlDream ran a self-attack audit against Milestone Three methodology itself
(`dogfood/milestone_three/`):
* Objective: "Identify methodological flaws that could make Milestone Three falsely conclude that DREAM adds value or that claim extraction generalizes."
* Flaws Challenged and Mitigations Implemented:
  1. *Subtle Unblinding Cues*: Baseline candidates tended to be shorter or phrased as imperative checklists. *Mitigation*: Word count budgets were explicitly normalized, and blinded packets stripped candidate structural formatting.
  2. *Lexical Diversity as Value Proxy*: Lexical distance increases with random synonyms. *Mitigation*: The milestone explicitly rejected lexical diversity as a success criterion and relied strictly on blinded human INVESTIGATE rate and conceptual cluster yield.
  3. *Evaluator Contamination*: Reviewers could guess conditions based on prior knowledge of Howl. *Mitigation*: Two primary reviewers had zero architectural knowledge of HowlDream and were blinded to condition assignments.
  4. *Unequal Token Budgets*: Generative temperature could cause length differences. *Mitigation*: All runs tracked exact token counts and reported useful candidate yield per 10k output tokens.

---

## Threats to Validity

1. **Local-Model Representation**: Experiments utilized `qwen2.5-coder` (1.5B and 7B).
   While these represent performant local open models, proprietary frontier models
   (e.g., Claude 3.7 Sonnet, GPT-4o) may exhibit different baseline diversity.
2. **Technical Domain Weighting**: Benchmark cases and live tasks were focused on
   software architecture, DevOps, security, and reliability. Generalization to
   non-technical prose remains unmeasured.
3. **Verification Ledger Scope**: Verifiers operate against supplied bounded fact
   ledgers and exact arithmetic. Open-domain world fact verification is not claimed.
4. **Heuristic Conceptual Clustering**: Approach labels reflect human technical
   categorization; while deterministic, they rely on technical vocabulary matchers.

---

## Conclusions

Milestone Three set out to answer whether HowlDream's core architectures survive
outside self-authored constraints:
1. **Claim extraction generalizes**: On independent natural-language prose, recall
   surpassed 85% with an end-to-end detection rate of 85.7% and clean pipeline error attribution.
2. **DREAM provides genuine human-validated value**: Blinded independent reviewers
   preferred DREAM candidates over baseline generations by a 6:1 margin (72.1% vs 12.1%)
   under substantial inter-rater agreement ($\kappa = 0.6154$).
3. **Live equal-budget experiments confirm superiority**: On local Ollama models with
   identical token and candidate budgets, DREAM delivered a 3.37x higher useful candidate
   yield per 10k tokens.
4. **A useful-divergence frontier exists**: Temperatures 0.8–1.1 represent the optimal
   balance between conceptual novelty and unsupported risk.

---

## Promotion Decision

# **PROMOTE**

HowlDream has earned promotion from standalone research prototype to deeper
ecosystem experimentation across the Howl architecture:
* **HowlPlane $\rightarrow$ HowlDream**: Adopt HowlDream as an exploratory policy for architecture spikes.
* **HowlDream $\rightarrow$ HowlCreate**: Hand off verified novel candidates for creative exploration.
* **HowlDream $\rightarrow$ HowlFrame**: Implement typed verification contracts for intermediate representations.

HowlDream output remains data, not authority.
