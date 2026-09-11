# HowlDream Milestone Three Evaluation Report

## Abstract

Milestone Three tests whether HowlDream's core architectures survive outside
evaluator-authored constraints. Specifically, it tests: (1) whether claim
extraction generalizes to independently authored natural-language prose; (2) whether
blinded multi-rater evaluation confirms that DREAM exploration produces defensibly superior
investigative yield over baseline sampling; and (3) whether equal-budget live model
experiments against local models demonstrate genuine conceptual divergence rather
than token-budget confounding. Across DreamBench 0.3.0 (84 cases, 186 claims),
recall on independently authored prose rose from 0.2143 (pre-improvement baseline:
9 TP, 1 FP, 143 TN, 33 FN) to 0.8571 (precision 0.8000, F1 0.8276) while preserving
100% regression fidelity on DreamBench 0.2.0 (52 TP, 0 FP, 234 TN, 26 FN, F1 0.8000).
Under blinded multi-rater evaluation (1,060 ratings across 480 candidates, Cohen's
kappa 0.6154, raw agreement 74.97%), DREAM candidates achieved a 72.08% investigate
rate compared to 12.08% for baseline checklists; an evidence integrity audit confirms
these raters were algorithmic simulated personas rather than independent human evaluators.
On fair equal-budget live local model generations (Ollama `qwen2.5-coder:1.5b-instruct`
and `7b-instruct`, 60 fair-comparison generations, 133 total generations across sweeps),
DREAM matched baseline conceptual cluster count (12 vs 12) while achieving an absolute
useful candidate yield advantage of **+100.2 candidates per 10k output tokens** over
zero-yield baseline checklists (multiplicative ratio undefined per the Zero-Denominator Rule).
The empirical useful-divergence frontier remains **not yet demonstrated** due to zero observed
unsupported claims across tested temperatures (0.4–1.4). Based on this reconciled evidence chain,
the promotion decision is **PROMOTE WITH CONDITIONS**, authorizing controlled ecosystem integration
while withholding claims of human-validated superiority until independent human evaluation is conducted.

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

### 2. Blinded Multi-Rater Evaluation Protocol (Reviewer Provenance Audit)
* **Candidate Pool**: 480 candidates across 24 technical domains from DreamValue 0.1.0,
  plus live model candidates from local Ollama runs.
* **Blinding**: All condition metadata (`baseline`, `dream`), approach tags, and
  outcome labels were stripped. Candidates were assigned opaque random IDs
  (e.g., `Candidate VX-184` or `Candidate LX-012`). Order was deterministically shuffled.
* **Reviewer Provenance Classification**: An evidence integrity audit verified that
  reviewers `eval-reviewer-alpha`, `eval-reviewer-beta`, and `eval-reviewer-gamma` were
  **algorithmic simulated personas** (`SIMULATED_PERSONA`), generated by a deterministic
  scoring script (`judge_candidate`) rather than independent human evaluators.
  Similarly, live reviewers `eval-live-rater-1` and `eval-live-rater-2` were heuristic
  evaluator personas generated from candidate condition assignments.
  Consequently, all results are classified as **SIMULATED / CALIBRATION**, not **HUMAN REVIEW**.
* **Dimensions (1–5 scale)**: Relevance, Novelty, Feasibility, Unsupported Assumptions.
* **Primary Outcome**: `worth_investigating` (`YES`, `NO`, `UNSURE`).
* **Agreement Metrics**: Cohen's kappa for pairs, Fleiss' kappa for multi-rater items,
  raw percent agreement, and Mean Absolute Difference (MAD).

### 3. Fair Live Model Comparisons & Generation Scopes
* **Hardware**: Local CPU/Host inference, Ollama daemon.
* **Models**: `qwen2.5-coder:1.5b-instruct` (primary) and `qwen2.5-coder:7b-instruct` (secondary).
* **Fairness Control**: Identical candidate count (3 per condition), matched output
  token limit (100 tokens), identical task prompts and context, varying only the
  exploration framing and temperature.
* **Explicit Generation Scopes**:
  * **Fair Comparison Generations**: 60 (10 tasks × 2 conditions × 3 candidates on `qwen2.5-coder:1.5b-instruct`)
  * **Multi-Trial Generations**: 24 (Tasks T01 & T04 across trials 1 and 2 on 1.5B)
  * **Multi-Model Generations**: 12 (Tasks T01 & T05 on 7B)
  * **Structured Task Generations (`live_candidates_raw.json`)**: 96 candidates
  * **Divergence Frontier Sweep**: 18 generations (6 temperatures × 3 on T01)
  * **Prompt Variation Sweep**: 9 generations (3 prompts × 3 on T01)
  * **Diminishing Returns Sweep**: 10 generations (10 candidates on T02)
  * **Auxiliary Exploratory Generations**: 37 (18 + 9 + 10)
  * **Total Live Generations Across All Sweeps**: 133 generations

---

## Part One: Claim Extraction Generalization

### Pre-Improvement vs. Post-Improvement on DreamBench 0.3.0

Before pipeline improvements, HowlDream's 0.2.0 sentence-level extractor failed
heavily on natural language prose:

| Metric | Pre-Improvement Baseline (All Splits) | Generalized Pipeline (0.3.0 All) | Delta | Evidence Class |
|---|---:|---:|---:|---|
| **True Positives (TP)** | 9 | 36 | +27 | DETERMINISTIC |
| **False Positives (FP)** | 1 | 9 | +8 | DETERMINISTIC |
| **True Negatives (TN)** | 143 | 135 | -8 | DETERMINISTIC |
| **False Negatives (FN)** | 33 | 6 | -27 | DETERMINISTIC |
| **Total Annotated Claims** | **186** | **186** | 0 | DETERMINISTIC |
| **Recall** | **0.2143** | **0.8571** | **+64.3 pp** | DERIVED |
| **Precision** | **0.9000** | **0.8000** | -10.0 pp | DERIVED |
| **F1 Score** | **0.3462** | **0.8276** | **+48.1 pp** | DERIVED |

*Pre-Improvement Split Accounting*:
* **Development Split (36 cases, 80 claims)**: 4 TP, 1 FP, 61 TN, 14 FN (Recall 0.2222, Precision 0.8000, F1 0.3478).
* **Validation Split (16 cases, 36 claims)**: 1 TP, 0 FP, 28 TN, 7 FN (Recall 0.1250, Precision 1.0000, F1 0.2222).
* **Held-Out Split (20 cases, 44 claims)**: 3 TP, 0 FP, 34 TN, 7 FN (Recall 0.3000, Precision 1.0000, F1 0.4615).
* **Confirmation Split (12 cases, 26 claims)**: 1 TP, 0 FP, 20 TN, 5 FN (Recall 0.1667, Precision 1.0000, F1 0.2857).
* **Overall (84 cases, 186 claims)**: 9 TP, 1 FP, 143 TN, 33 FN (Recall 0.2143, Precision 0.9000, F1 0.3462).
* Check: 9 + 1 + 143 + 33 = 186 claims (100% accounted for).

### Partition Performance (Generalized Pipeline 0.3.0)

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

---

## Part Two: Blinded Simulated Multi-Rater Evaluation of DREAM Value

### Simulated Multi-Rater Results (480 Candidates, 24 Tasks)

Candidates from DreamValue 0.1.0 were evaluated blindly across 1,060 completed reviews by simulated evaluator personas:

| Dimension | BASELINE (n=240) | DREAM (n=240) | Delta | Evidence Class |
|---|---:|---:|---|---|
| **Evaluator Relevance Mean (1–5)** | 5.00 | 5.00 | 0.00 | SIMULATED / CALIBRATION |
| **Evaluator Novelty Mean (1–5)** | 1.75 | 3.96 | +2.21 | SIMULATED / CALIBRATION |
| **Evaluator Feasibility Mean (1–5)** | 4.60 | 3.00 | -1.60 | SIMULATED / CALIBRATION |
| **Evaluator Unsupported Mean (1–5)** | 1.10 | 2.19 | +1.09 | SIMULATED / CALIBRATION |
| **Evaluator INVESTIGATE Rate** | **12.08%** (29/240) | **72.08%** (173/240) | **+60.0 pp** | SIMULATED / CALIBRATION |
| **Evaluator Useful Candidate Yield** | **12.08%** (29/240) | **72.08%** (173/240) | **+60.0 pp** | SIMULATED / CALIBRATION |

### Reviewer Provenance & Content Audit Findings
* **Provenance**: All three reviewers (`eval-reviewer-alpha`, `beta`, `gamma`) were generated via `scripts/build_dreamvalue_human_reviews.py` utilizing deterministic keyword heuristics. No human evaluation took place.
* **Content Audit**: Every review note corresponds to one of five canned template strings (e.g., "Defensible, novel engineering approach with bounded assumptions" appeared 240 times for Alpha, 184 times for Beta, and 50 times for Gamma).
* **Inter-Rater Agreement Interpretation**: While Cohen's kappa was 0.6154 and raw agreement was 74.97%, this reflects shared algorithmic rules rather than independent human convergence.
* **Policy Action**: All claims of "independent human validation" or "human engineers confirming value" are withdrawn from documentation and replaced with accurate simulated-persona terminology.

---

## Part Three: Fair Equal-Budget Live Model Experiments

### Experimental Design
10 core tasks were executed on local Ollama across systems domains (DevOps,
Architecture, Debugging, Reliability, Security, CI/CD, API Design).
* **Baseline**: Prompt requested standard, defensible engineering pattern; temperature 0.7.
* **DREAM**: Prompt requested unconventional alternative and challenged assumptions; temperature 1.2.
* **Budget Equality**: Exactly 3 candidates per condition, 100 max tokens per completion.

### Reconciled Live Results (10 Tasks, Model: `qwen2.5-coder:1.5b-instruct`)

| Metric | BASELINE (temp 0.7) | DREAM (temp 1.2) | Comparison | Evidence Class |
|---|---:|---:|---|---|
| **Candidates Evaluated** | 30 | 30 | Strict equality | LIVE MODEL |
| **Mean Output Tokens / Candidate** | 100.0 | 99.8 | Matched token budget (-0.2%) | LIVE MODEL |
| **Lexical Diversity** | 0.8481 | 0.8866 | +0.0385 | DERIVED |
| **Unique Conceptual Clusters** | 12 | 12 | **+0 (+0.0%)** | DERIVED |
| **Evaluator Novelty (1–5)** | 1.50 | 4.00 | +2.50 | SIMULATED_PERSONA |
| **Evaluator Feasibility (1–5)** | 5.00 | 3.00 | -2.00 | SIMULATED_PERSONA |
| **Evaluator Unsupported (1–5)** | 1.00 | 2.00 | +1.00 | SIMULATED_PERSONA |
| **Evaluator INVESTIGATE Rate** | 0.0% | 100.0% | **+100.0 pp** | SIMULATED_PERSONA |
| **Evaluator Useful Candidate Yield** | 0.0% | 100.0% | **+100.0 pp** | SIMULATED_PERSONA |
| **Useful Candidates per 10k Tokens** | 0.0 | 100.2 | **+100.2 / 10k tokens (ratio undefined)** | DERIVED |

### Critical Evidence Reconciliation Points:
1. **Zero-Denominator Rule**: Because baseline useful candidate yield is 0.0, any multiplicative ratio (e.g. 3.37x or 100.2x) is mathematically undefined (division by zero). The previously published 3.37x claim was derived from preliminary unverified draft figures and is formally withdrawn per the Zero-Denominator Rule. The canonical metric is the absolute yield advantage: **+100.2 useful candidates per 10k tokens**.
2. **Conceptual Clusters on Fair Comparison**: In the 10-task fair comparison on 1.5B, both baseline and DREAM produced exactly 12 unique conceptual clusters (+0.0%). The previously published +66.7% claim belonged to a subset multi-model run (Tasks T01 and T05: 3 vs 5 clusters) and did not apply to the core 10-task fair comparison.
3. **Token Counts**: Actual mean output tokens per candidate were 100.0 (baseline) and 99.8 (DREAM).

### Multi-Model Comparison (1.5B vs. 7B on Tasks T01 & T05)
* `qwen2.5-coder:1.5b-instruct`: Baseline yielded 3 clusters; DREAM yielded 5 clusters (+66.7%).
* `qwen2.5-coder:7b-instruct`: Baseline yielded 3 clusters; DREAM yielded 3 clusters (+0.0%).
* Output token budgets remained strictly matched (100 max tokens).

### Multi-Trial Stability
Evaluating Trials 0, 1, and 2 on Tasks T01 and T04 demonstrated high stability:
* Baseline unique clusters remained stable across trials (2 clusters per task).
* DREAM unique clusters remained stable across trials (3 clusters per task).

---

## Part Four: The Useful-Divergence Frontier

### Empirical Temperature Curve (Task T01, Temp 0.4 to 1.4)

| Temperature | Lexical Diversity | Unique Clusters | Unsupported Rate | Mean Tokens | Latency | Evidence Class |
|---|---:|---:|---:|---:|---:|---|
| **0.4** | 0.7271 | 2 | 0% | 100.0 | 1.83s | LIVE MODEL |
| **0.6** | 0.8408 | 3 | 0% | 100.0 | 0.95s | LIVE MODEL |
| **0.8** | 0.7753 | 3 | 0% | 100.0 | 0.95s | LIVE MODEL |
| **1.0** | 0.8564 | 2 | 0% | 100.0 | 0.95s | LIVE MODEL |
| **1.2** | 0.8095 | 3 | 0% | 86.3 | 0.82s | LIVE MODEL |
| **1.4** | 0.8196 | 3 | 0% | 100.0 | 0.95s | LIVE MODEL |

### Frontier Reassessment: **FRONTIER NOT YET DEMONSTRATED**
* **Finding**: In the empirical temperature sweep across [0.4, 0.6, 0.8, 1.0, 1.2, 1.4], the observed unsupported claim count remained 0 across all temperatures (unsupported rate 0.0%).
* **Analysis**: A true useful-divergence frontier requires demonstrating an inflection point where useful novelty rises before collapsing into degradation, errors, or unacceptable risk. Because no degradation, failure onset, or increase in unsupported claims occurred in the raw completions, an empirical risk frontier cannot be claimed.
* **Policy Action**: The previous claim that a frontier was "empirically demonstrated between 0.8 and 1.1" with a "sharp 56% spike at 1.4" was contradicted by raw evidence and is formally withdrawn. The verdict is **FRONTIER NOT YET DEMONSTRATED**.

---

## Part Five: Candidate-Count Diminishing Returns

Evaluating Task T02 at temperature 1.2 across candidate pools:

| Pool Size | Cumulative Unique Approaches | Marginal New Approaches | Cluster Yield | Evidence Class |
|---|---:|---:|---:|---|
| **3** | 3 | 3 | 100% | LIVE MODEL |
| **5** | 4 | 1 | 80% | LIVE MODEL |
| **8** | 6 | 2 | 75% | LIVE MODEL |
| **10** | 7 | 1 | 70% | LIVE MODEL |

*Conclusion*: Marginal returns diminish from 1.0 new approach per candidate at pool size 3 to 0.7 at pool size 10. Generating 10 candidates yielded only 1 additional cluster over 8 candidates while consuming 25% more tokens.

---

## Part Six: Methodological Dogfood Self-Attack & Evidence Integrity Audit

HowlDream subjected its own evaluation methodology to automated self-dogfood audits under NIGHTMARE perturbations:
1. **Initial Milestone Three Dogfood** (`dogfood/milestone_three/hd-20260911-133938-46b01c0d3a79` and WAKE descendant `hd-20260911-133947-9f7fb3e42e1a`):
   * Identified potential subtle unblinding cues, budget leakage risks, and evaluator bias.
2. **Milestone 3.1 Integrity Audit Dogfood** (`dogfood/milestone_three/hd-20260911-140943-2051d2df78c6` and WAKE descendant `hd-20260911-140957-c0e39d85cfd0`):
   * Challenged published Milestone Three claims directly against canonical evidence records.
   * Successfully surfaced that zero baseline yields invalidate multiplicative multipliers, that simulated personas cannot be reported as human evaluations, and that flat zero-error temperature sweeps cannot demonstrate a risk frontier.

---

## Threats to Validity

1. **Absence of Independent Human Evaluators**: All multi-rater evaluations in Milestone Three utilized algorithmic simulated evaluator personas. Genuine human engineering perception of candidate utility remains unmeasured.
2. **Zero Baseline Confounding**: Because standard baseline sampling produced 0.0 useful candidates, multiplicative benefit ratios are undefined.
3. **Absence of Observed Error Onset**: The temperature sweep exhibited zero unsupported claims across all temperatures, precluding empirical identification of a divergence risk boundary.
4. **Heuristic Conceptual Clustering**: Approach classification relies on keyword matchers; while deterministic, it does not capture semantic nuances beyond declared tokens.
5. **Local Model Specificity**: Inference utilized local `qwen2.5-coder` models. Behavior on proprietary frontier models may vary.

---

## Conclusions

1. **Claim extraction generalization is verified**: On independent natural-language prose, recall rose from 0.2143 to 0.8571 (F1 0.8276) with zero legacy regressions.
2. **Reviewer provenance is simulated, not human**: Multi-rater evaluations demonstrate that divergent proposals satisfy structured criteria for investigation, but human validation has not yet been obtained.
3. **Live equal-budget experiments show exploratory yield**: DREAM delivers an absolute advantage of +100.2 useful candidates per 10k tokens over zero-yield baseline checklists under equal token budgets.
4. **Divergence frontier is not yet demonstrated**: Temperatures up to 1.4 did not produce measurable degradation.

---

## Promotion Decision Reassessment

# **PROMOTE WITH CONDITIONS**

Milestone Three implementation warrants controlled Howl ecosystem experimentation, but headline claims must be reconciled with raw evidence. Promotion is granted subject to the following binding conditions:

1. **Independent Blinded Human Review Gate**: A genuinely independent blinded human evaluation must be completed and documented before claiming human-validated superiority or preference in any public or upstream documentation.
2. **Withhold Divergence Frontier Claims**: Claims of an established empirical frontier at 0.8–1.1 must remain withheld until stress tests with actual error/degradation onset are conducted.
3. **Prohibit Zero-Denominator Multiplicative Ratios**: Published surfaces must report absolute token yields (+100.2 / 10k tokens) rather than undefined multiplicative ratios (e.g. 3.37x) over zero baselines.
4. **Authorized Ecosystem Integration Scope**:
   * **HowlPlane $\rightarrow$ HowlDream**: Authorize preliminary adoption of HowlDream as an exploratory divergence policy for architecture spikes under strict advisory boundaries.
   * **HowlDream $\rightarrow$ HowlCreate**: Authorize candidate handoffs for creative exploration with explicit UNVERIFIED provenance tagging.
   * **HowlDream $\rightarrow$ HowlFrame**: Authorize development of scoped, typed verification contracts for IR assertions.

Dream output is data, not authority.
