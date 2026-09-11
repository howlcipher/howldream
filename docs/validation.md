# Milestone verification evidence

Milestone Two local suite: 53 passed, zero failures and zero skips on Python
3.14.4. Ruff formatting/check, Flake8 with README flags, mypy, wheel and source
distribution build, Bandit, and dependency audit pass. The historical Milestone
One 14-fixture result remains in `dogfood/benchmark.json`.

DreamBench 0.2.0 has 156 cases and 312 claims. Overall: 52 TP, 0 FP, 234 TN,
26 FN, precision 1.0, recall 0.6667, and F1 0.8. Primary held-out recall is 0;
confirmation recall is 1.0. DreamValue evaluates 24 tasks with equal 240-candidate
pools. Canonical evidence is under `evaluation/results/`.

CLI coverage includes validation, generation, DREAM, NIGHTMARE, WAKE, replay,
inspection, comparison, reports, benchmark listing and split execution, DreamValue,
malformed inputs, split isolation, zero denominators, claim matching, duplicate
groups, curves, blind packets, and annotation-oracle isolation.

Pages renders at 375, 768 and 1440 pixels with title, description, landmarks,
keyboard skip link, fragment navigation, and no document overflow. Site evaluation
JSON is generated from canonical artifacts.

Bandit reports zero medium/high findings. Dependency audit reports no known
vulnerabilities; the unpublished local package itself is skipped. A local Ollama
audit completed with retained provider settings, usage, latency, outputs, and
limitations. The earlier sandbox-blocked attempt remains as PARTIAL evidence.

The independent delegated reviewers exhausted their service quota before returning
findings. A primary-agent falsification review found and removed annotation-oracle
leakage; a regression proves predictions derive from observed response extraction.
No independent human DreamValue ratings are claimed.

## Milestone 3.1 evidence integrity verification

Milestone 3.1 local suite: 67 passed, zero failures and zero skips on Python 3.14.4.
Ruff format/check, Flake8 with README flags, mypy, wheel and source distribution build,
Bandit, and pip-audit pass cleanly.

DreamBench 0.3.0 contains 84 cases and 186 claims. Pre-improvement overall baseline:
9 TP, 1 FP, 143 TN, 33 FN (recall 0.2143, precision 0.9000, F1 0.3462). Post-improvement:
36 TP, 9 FP, 135 TN, 6 FN (recall 0.8571, precision 0.8000, F1 0.8276), preserving 100%
regression fidelity on DreamBench 0.2.0 (F1 0.8000).

DreamValue blinded multi-rater evaluation evaluated 480 candidates across 24 tasks
(1,060 completed reviews, Cohen's kappa 0.6154, raw agreement 74.97%). Evaluators
`eval-reviewer-alpha`, `beta`, and `gamma` were classified as `SIMULATED_PERSONA`
(algorithmic heuristic personas); no human evaluation is claimed.

Live model experiments on local Ollama (`qwen2.5-coder:1.5b-instruct` and `7b-instruct`):
60 fair-comparison generations (133 total live generations across sweeps). Conceptual
clusters on fair comparison were equal (12 vs 12). Baseline useful yield was 0.0;
DREAM useful yield was 100.2 / 10k tokens (+100.2 / 10k tokens absolute difference;
multiplicative ratio undefined per Zero-Denominator Rule). Empirical divergence frontier
is reclassified to FRONTIER NOT YET DEMONSTRATED due to 0% unsupported claims across
temperatures 0.4 to 1.4.

Automated consistency regression tests (`tests/test_evidence_integrity.py`) enforce that
all presentation surfaces match canonical JSON and manifest records.
Decision: PROMOTE WITH CONDITIONS.

