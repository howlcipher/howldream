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
