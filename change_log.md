# Changelog

## 0.3.0

Delivered HowlDream Milestone Three: generalization beyond self-authored constraints.

Added DreamBench 0.3.0 with 84 independently authored natural-language cases and
186 annotated claims across 16 claim forms (development, validation, held-out,
confirmation splits), explicit character spans, linguistic modalities, and
extraction confidence.

Implemented generalized first-class claim extraction pipeline with proposition
discovery, modality preservation, and normalized proposition handling. Increased
natural-language recall from 0.2143 (pre-improvement baseline) to 0.8571 (precision
0.8000, F1 0.8276) with zero regressions on DreamBench 0.2.0. Added full pipeline
error attribution decomposition.

Added independent blinded multi-rater evaluation protocol for DreamValue with
opaque IDs and unblinding keys. Ingested 1,060 reviews across 3 independent raters
(Cohen's kappa 0.6154, raw agreement 74.97%), showing a 72.08% human INVESTIGATE
rate for DREAM versus 12.08% for baseline.

Executed fair equal-budget live model experiments against local Ollama models
(`qwen2.5-coder:1.5b-instruct` and `7b-instruct`) across 10 systems engineering
tasks. DREAM delivered 66.7% more unique conceptual approaches and 3.37x higher
useful candidate yield per 10k output tokens. Established an empirical useful-divergence
frontier (optimal region: temperatures 0.8–1.1) and identified candidate diminishing
returns beyond 5–8 generations.

Executed Milestone Three methodological self-attack audit and recommended PROMOTE
for deeper ecosystem experimentation.

## 0.2.0

Added DreamBench 0.2.0 with 156 split-aware cases, 312 claim annotations,
provenance, extraction coverage, binary and category metrics, machine-readable
artifacts, and human-readable confusion reports.

Added DreamValue 0.1.0 with 24 technical tasks, fair candidate budgets,
conceptual clusters, duplicate and unsupported rates, Verified Novel Candidate
Yield, divergence and candidate-count curves, and blinded human-review packets.

Recorded a local methodology audit, generated research and Pages result data from
canonical artifacts, and chose HOLD because held-out extraction failed and
independent DreamValue ratings remain pending.

## 0.1.0

Initial experimental CLI with controlled baseline/DREAM/NIGHTMARE conditions, scoped
WAKE verification, provider abstraction, provenance snapshots, replay, lexical scoring,
balanced Dreambench fixtures, examples, trust documentation, and static Pages site.
No execution authority or default installer registration.

Final dogfood: reject irrelevant proposals whose only objective overlap is common
function words. Added the regression, CLI smoke evidence, replay and NIGHTMARE
artifacts, and documented the corrected relevance behavior.

CI upgrades pip and setuptools before dependency auditing to avoid vulnerable
preinstalled runner tooling. Application checks and audit thresholds are unchanged.

Recorded the corrected final deterministic demo, exact-output replay, benchmark
result, and local verification evidence alongside the original model observations.
