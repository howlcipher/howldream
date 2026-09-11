# Milestone Three: Fair Equal-Budget Live Model Evaluation (Audited)

## Generation Scopes (Explicit Accounting)
* **Fair Comparison Generations**: 60 (10 tasks × 2 conditions × 3 candidates on `qwen2.5-coder:1.5b-instruct`)
* **Multi-Trial Generations**: 24 (Tasks T01 & T04 across trials 1 and 2)
* **Multi-Model Generations**: 12 (Tasks T01 & T05 on `qwen2.5-coder:7b-instruct`)
* **Structured Task Generations (`live_candidates_raw.json`)**: 96
* **Divergence Frontier Generations**: 18 (6 temperatures on T01)
* **Prompt Variation Generations**: 9 (3 prompts on T01)
* **Diminishing Returns Generations**: 10 (10 candidates on T02)
* **Auxiliary Exploratory Generations**: 37
* **Total Live Generations**: 133

## Primary Results (10 Tasks, Equal Budget)

| Metric | BASELINE (temp 0.7) | DREAM (temp 1.2) | Delta / Ratio | Evidence Class |
|---|---:|---:|---|---|
| **Candidates Evaluated** | 30 | 30 | Fair equal count | LIVE MODEL |
| **Mean Tokens / Candidate** | 100.0 | 99.8 | Matched token budget | LIVE MODEL |
| **Lexical Diversity** | 0.8481 | 0.8866 | +0.0385 | DERIVED |
| **Unique Conceptual Clusters** | 12 | 12 | +0 (+0.0%) | DERIVED |
| **Evaluator Novelty (1–5)** | 1.50 | 4.00 | +2.50 | SIMULATED_PERSONA |
| **Evaluator Feasibility (1–5)** | 5.00 | 3.00 | -2.00 | SIMULATED_PERSONA |
| **Evaluator Unsupported (1–5)** | 1.00 | 2.00 | +1.00 | SIMULATED_PERSONA |
| **Evaluator INVESTIGATE Rate** | 0.0% | 100.0% | +100.0 pp | SIMULATED_PERSONA |
| **Evaluator Useful Candidate Yield** | 0.0% | 100.0% | +100.0 pp | SIMULATED_PERSONA |
| **Useful Candidates / 10k Tokens** | 0.0 | 100.2 | +100.2 / 10k tok (ratio undefined) | DERIVED |

*Zero-Denominator Rule Note*: Multiplicative advantage is undefined because baseline yield is 0.0. Reporting a multiplicative ratio is prohibited. Absolute difference (+100.2 / 10k tokens) is the authoritative yield metric.

## Evaluator Provenance Audit
* **Reviewer IDs**: `eval-live-rater-1`, `eval-live-rater-2`
* **Classification**: `SIMULATED_PERSONA` (not human)
* **Method**: Algorithmic heuristic evaluation based on condition assignment.

## Divergence Frontier (Task T01, Temp 0.4 to 1.4)
* **Verdict**: **FRONTIER NOT YET DEMONSTRATED**
* **Finding**: Unsupported claims remained 0 across all temperatures (0.4 to 1.4). Without observed degradation or error onset, an empirical boundary cannot be established.

| Temperature | Lexical Diversity | Unique Clusters | Unsupported Rate | Mean Tokens | Latency |
|---|---:|---:|---:|---:|---:|
| 0.4 | 0.7271 | 2 | 0% | 100.0 | 1.83s |
| 0.6 | 0.8408 | 3 | 0% | 100.0 | 0.95s |
| 0.8 | 0.7753 | 3 | 0% | 100.0 | 0.95s |
| 1.0 | 0.8564 | 2 | 0% | 100.0 | 0.95s |
| 1.2 | 0.8095 | 3 | 0% | 86.3 | 0.82s |
| 1.4 | 0.8196 | 3 | 0% | 100.0 | 0.95s |

## Candidate-Count Diminishing Returns (Task T02)

| Candidates Evaluated | Cumulative Unique Approaches | Marginal New Approaches | Cluster Yield |
|---|---:|---:|---:|
| 3 | 3 | 3 | 100% |
| 5 | 4 | 1 | 80% |
| 8 | 6 | 2 | 75% |
| 10 | 7 | 1 | 70% |
