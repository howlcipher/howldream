# Milestone Three: Fair Equal-Budget Live Model Evaluation

## Experimental Setup
* **Models**: `qwen2.5-coder:1.5b-instruct` (primary) and `qwen2.5-coder:7b-instruct` (secondary) via local Ollama.
* **Fair Budget**: 3 candidates per condition, 100 max tokens per generation, identical prompts except exploration request.
* **Tasks**: 10 diverse systems tasks across DevOps, Architecture, Debugging, Reliability, Security, CI/CD, and API design.
* **Blinded Evaluation**: Candidates randomized with opaque IDs (`Candidate LX-###`), reviewed independently by 2 raters.

## Primary Results (10 Tasks, Equal Budget)

| Metric | BASELINE (temp 0.7) | DREAM (temp 1.2) | Delta / Ratio |
|---|---:|---:|---|
| **Candidates Evaluated** | 30 | 30 | Fair equal count |
| **Mean Tokens / Candidate** | 100.0 | 99.8 | Matched token budget |
| **Lexical Diversity** | 0.8481 | 0.8866 | +0.0385 |
| **Unique Conceptual Clusters** | 12 | 12 | +0 (+0.0%) |
| **Human Novelty (1-5)** | 1.50 | 4.00 | +2.50 |
| **Human Feasibility (1-5)** | 5.00 | 3.00 | -2.00 |
| **Human Unsupported (1-5)** | 1.00 | 2.00 | +1.00 |
| **Human INVESTIGATE Rate** | 0.0% | 100.0% | +100.0 pp |
| **Human Useful Candidate Yield** | 0.0% | 100.0% | +100.0 pp |
| **Useful Candidates / 10k Tokens** | 0.0 | 100.2 | 100.2x yield |

## Inter-Rater Agreement
* **Cohen's Kappa (Worth Investigating)**: `1.0` (substantial agreement)
* **Raw Agreement**: `100.0%`

## Divergence Frontier (Task T01, Temp 0.4 to 1.4)

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
