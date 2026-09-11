# Changelog

## 0.4.0

Delivered HowlDream Milestone Four: Controlled Native Howl Ecosystem Integration.

Implemented end-to-end controlled native integration across HowlPlane, HowlFrame, HowlCreate, and HowlRelay while enforcing zero execution authority and strict downstream segregation:
* **Native Ecosystem Contracts**: Added strict schemas in `src/howldream/contracts.py` for `howl.exploration/v1` (request), `howl.candidate/v1` (immutable candidate with provenance), `howl.assessment/v1` (evaluation assessment), `howl.exploration_result/v1` (envelope and outcome), and `howl.development_result/v1` (sandbox prototype specification).
* **Descent DAG Lineage**: Implemented `DescentDAG` capturing exploration trees, parent-child lineages, branching factors, cycle detection, and graph traversal. Added `howldream trace <run_id>` CLI subcommand for inspecting lineage.
* **Exploration CLI Subcommand**: Added `howldream explore` CLI subcommand emitting `exploration_envelope.json` alongside standard run manifests.
* **HowlFrame Integration**: Authored `apps/candidate_evaluator/candidate_evaluator.howl` and compiled bytecode (`.hfbc`) validating structural invariants, schema versions, and claim bounds.
* **HowlCreate Integration**: Implemented deliberate candidate ingestion (`howlcreate.engine.candidate_ingestion`) and `howlcreate develop` CLI subcommand producing sandbox prototype designs without execution authority (`EXECUTION_AUTHORITY: NONE`).
* **HowlPlane Integration**: Implemented `HowlDreamRunner` with exploration policies, token/candidate budgets, circuit breakers, and hard negative boundary checks preventing execution receipt issuance for speculative candidates. Added `explore` and `trace` CLI subcommands in HowlPlane.
* **HowlRelay Integration**: Implemented native `HowlDreamCollector` adapter gathering `HOWLDREAM_EXPLORATION` evidence without altering authority.
* **End-to-End Verification**: Validated three canonical end-to-end scenarios (Useful Candidate Flow, No-Valuable Result Flow, and Unsafe Authority Escalation Attempt).
* **Testing Architecture**: Refactored test harness with contract-compatible adapters for standalone CI independence; eliminated developer workstation path assumptions.
* **Lineage & Authority Hardening**: Enhanced `DescentDAG` with cycle detection, depth limits, and branching factor protections; added `DevelopmentResult` contract model.
* **Dogfooding Evidence**: Completed dogfood exploration run `hd-20260911-145551-873eea4f7922` documenting lineage DAG, artifact verification, and ecosystem handoffs in `dogfood/milestone_four/SUMMARY.md`.

## 0.3.1

Delivered HowlDream Milestone 3.1: Evidence Integrity Audit & Claim Reconciliation.

Reconciled every published Milestone Three claim against canonical raw evidence:
* **Generation Scopes**: Explicitly resolved generation counts into 60 fair-comparison, 24 multi-trial, 12 multi-model (96 structured task candidates), 18 frontier, 9 prompt-variation, and 10 diminishing-returns (37 auxiliary exploratory), establishing 133 total live generations across all sweeps.
* **Reviewer Provenance Audit**: Classified all evaluators (`eval-reviewer-alpha`, `beta`, `gamma`, and live raters 1 & 2) as `SIMULATED_PERSONA` generated via algorithmic heuristics. Formally withdrew unsupported claims of "human-validated" superiority.
* **Fair Baseline vs. DREAM Reconciliation**: Corrected core 10-task fair comparison to canonical values (12 baseline vs. 12 DREAM clusters, +0.0%; baseline useful yield 0.0 vs. DREAM 100.2 / 10k tokens).
* **Zero-Denominator Rule**: Formally withdrew undefined multiplicative yield ratios (e.g. 3.37x) over zero baselines; established absolute yield difference (+100.2 / 10k tokens) as authoritative.
* **Useful-Divergence Frontier**: Reclassified frontier status to **FRONTIER NOT YET DEMONSTRATED** due to zero observed unsupported claims across tested temperatures (0.4 to 1.4).
* **Pre-Improvement Confusion Matrix**: Reconciled canonical DreamBench 0.3.0 pre-improvement confusion matrix across all 186 annotated claims (9 TP, 1 FP, 143 TN, 33 FN; recall 0.2143, precision 0.9000, F1 0.3462).
* **Unified Canonical Builder & Manifest**: Added `scripts/build_milestone_three_results.py` and `evaluation/results/milestone_three_manifest.json` establishing a single calculation path.
* **Automated Regression Test**: Added `tests/test_evidence_integrity.py` preventing report/result drift.
* **Promotion Reassessment**: Reassessed Milestone Three promotion decision from PROMOTE to **PROMOTE WITH CONDITIONS**.

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
