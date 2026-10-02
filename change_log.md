# Changelog

## Unreleased

Pinned the final reviewed provider core with portable command tests. CI preserves
`HOWL_FORBID_LOCAL_INFERENCE=1` for all verification commands.
HTTP fixtures use mocked remote-shaped endpoints; cached local-provider rejection
is tested without lifting the local-inference prohibition.

## 0.4.3

Closes `issues.md` items 1–3 with cross-repo evidence, and corrects a stale claim
this session initially repeated before re-verifying it live:

* **Item 1 closed**: howlframe (PR #41, merged) vendored the `schemas/` generated in
  0.4.2 into `contracts/howl/` and added a pure-Go `contract_test.go` validating a
  real `howl.exploration_result/v1` envelope and rejecting forged/malformed ones —
  the cross-language consumer test this item's acceptance criterion required, with no
  Python, no `howldream` import, and no network access at test time.
* **Item 2 closed**: howlplane (PR #101, merged) added
  `tests/test_howldream_live_integration.py`, driving `NativeHowlDreamProvider`
  against a real `howldream` install pinned to this repo's `bd10b18` commit, gated
  behind the pre-existing `HOWLPLANE_LIVE_PROVIDERS`/`HOWLPLANE_RUN_LIVE_TESTS`
  scaffolding. Verified in a real GitHub Actions run (not just locally): the pinned
  commit was cloned and installed fresh and all 3 live tests passed.
* **Item 3 closed — and a stale claim caught mid-session**: this session's initial
  recon repeated the prior report's claim that HowlFrame's `candidate_evaluator`
  branch was unmerged. Re-checking directly against `howlframe`'s actual `origin/main`
  found it had already been merged (PR #40, 2026-09-11T19:02:48Z) before this session
  began. Rather than trust that discovery either, independently re-verified it: fetched
  `howlframe` `main` fresh and ran `go test ./apps/candidate_evaluator/...` directly
  (5/5 subtests pass, including both authority-escalation rejections) before updating
  any documentation. `README.md`, `docs/ecosystem.md`, and `docs/architecture.md`'s
  "what actually runs today" tables are updated accordingly — this is the discipline
  the 0.4.1 correction established: verify live state, don't restate the last report.
* **Item 4 remains open**, and is explicitly *not* claimed as done here: HowlFrame's
  evaluator being merged does not by itself make the Milestone Four dogfood portable —
  neither HowlDream's nor HowlPlane's pipeline builds/invokes the compiled `.hfbc`
  automatically; both still require `HOWLFRAME_HFBC_PATH`/
  `HOWLFRAME_CANDIDATE_EVALUATOR_BC` pointed at a manually-built artifact. A
  reproducible run through the real bytecode from a fresh clone is the next
  highest-value gap.

## 0.4.2

Machine-readable `howl.*` contracts (issues.md item 1, in progress) and a real
`Provenance` model, in place of an untyped `dict[str, Any]`, on every envelope:

* **Generated JSON Schema**: `scripts/generate_schemas.py` generates
  `schemas/howl.{exploration,candidate,assessment,exploration_result,development_result}.v1.schema.json`
  from `src/howldream/contracts.py` via Pydantic `model_json_schema()`. Never
  hand-authored. `--check` mode regenerates into a temp dir and diffs against
  `schemas/`, wired into `.github/workflows/ci.yml` as drift detection.
* **`schemas/README.md`**: documents the authoritative source, the versioning/evolution
  policy (additive changes stay within `v1`; breaking changes get a new
  `schema_version` literal and file), and the contract distribution architecture
  decision (vendored copies pinned to a commit, evaluated against three alternatives).
* **Typed `Provenance` model**: replaced `provenance: dict[str, Any]` (no guarantees,
  every producer inventing its own ad hoc keys — confirmed by inspecting real usage in
  `engine.py`, `run_milestone_four_dogfood.py`, and downstream repos before making this
  change) with a `Provenance` model carrying the cross-cutting fields a downstream
  consumer actually needs (`run_id`, `producer_component`, `producer_version`,
  `model_or_provider`, `observation_kind`, `created_at`, `transformations`).
  Deliberately `additionalProperties: true` (unlike every other structural model in this
  file) since it's audit metadata, not an authority boundary — existing free-form
  provenance dicts from any producer remain valid. `engine.py`'s two producers now
  populate the canonical fields, including `observation_kind` derived from the real
  `provider_kind` selection (`SIMULATED` for the mock provider, `LIVE` otherwise).
* **`AUTHORITY_INVARIANT.md`**: states precisely which authority claims (`authority.
  executable`, `authority.type`, `trust`, `execution_authority`, `disposition`,
  `verification_status`, `schema_version`, any unknown/privileged field) are rejected
  by schema shape alone — provable without importing `howldream` — versus which require
  a runtime control (nested-payload authority smuggling, provenance forgery, forged
  HowlProof verdicts embedded in free-form fields).
* **`tests/test_authority_invariants.py`** (100 tests): proves every claim in
  `AUTHORITY_INVARIANT.md` at both the Pydantic layer and the generated-schema layer,
  across all five envelope families.
* **Documentation drift correction**: `docs/ecosystem.md`'s "Native Schemas" section
  previously hand-described field names (`goal`, `budget_candidates`, `seed_proposals`,
  `parent_candidate_id`, `state`, `run_dir`, `prototype_design`, `test_spec`, ...) that
  did not match the actual `contracts.py` fields (`objective`, `budget.max_candidates`,
  `trust`, `sandbox_prototype_design`, `test_specification`, ...). Replaced with a
  pointer to the generated schema files instead of a second hand-written copy that
  would only drift again.
* **Not yet closed**: issues.md item 1's acceptance bar requires a sibling repo to
  validate against the vendored schema in its own test suite without importing
  `howldream` — that consumer (HowlFrame, Go) is tracked separately and not yet merged
  as of this entry. Item 2 (HowlPlane CI gap) is unaffected by this change.

## 0.4.1

Milestone Four Evidence Integrity Correction. Reconciled the 0.4.0 "controlled native
integration" claims against the actual state of the sibling repositories rather than
restating the original entry, following the same discipline as the 0.3.1 audit:

* **HowlFrame claim withdrawn**: 0.4.0 stated HowlDream "authored
  `apps/candidate_evaluator/candidate_evaluator.howl` and compiled bytecode." This file
  exists only on an **unmerged** howlframe branch (`feat/milestone-four-candidate-evaluator`)
  and is not present on `main` in howlframe or anywhere in this repo. HowlDream's own
  `tests/test_end_to_end_ecosystem.py` runs an in-process Python reimplementation of the
  same rules as a stand-in; that is what actually executes today. Reclassified from
  "native integration" to "prototype pending merge in howlframe."
* **HowlCreate and HowlPlane claims qualified**: both `candidate_ingestion.develop_candidate()`
  (howlcreate) and `HowlDreamRunner`/`NativeHowlDreamProvider` (howlplane) are real, merged
  code, confirmed present and unit-tested in their own repos. However, neither cross-repo
  import path is exercised in either side's CI: HowlDream's CI never installs `howlcreate`
  (`tests/test_end_to_end_ecosystem.py` runs its `except ImportError` fallback stub
  unconditionally), and HowlPlane's CI never installs `howldream` (its tests inject a
  `DeterministicTestExplorationProvider` fake). Reclassified from "native integration" to
  "merged, CI-unverified via real import."
* **HowlRelay claim confirmed accurate**: `HowlDreamCollector` is real, merged, and
  genuinely exercised end-to-end without qualification — it is a pure file-contract
  reader with no package dependency on HowlDream, so it needed no correction.
* **"Eliminated developer workstation path assumptions" claim withdrawn**: 0.4.0 stated
  this outright. `scripts/run_milestone_four_dogfood.py` locates the HowlFrame bytecode
  via hardcoded, machine-specific relative paths
  (`repo_root.parents[0] / "worktrees" / "howlframe-milestone-four" / ...`), so the
  dogfood evidence backing this milestone (`dogfood/milestone_four/SUMMARY.md`) was a
  one-off run tied to this workstation's exact sibling-checkout layout, not something
  another clone or CI could reproduce. Replaced the hardcoded paths with a
  `HOWLFRAME_HFBC_PATH` environment variable and documented the script as a manual,
  local reproducibility aid rather than a CI-gated integration test.
* **HowlCreate CI-exercise gap closed**: added an `ecosystem-integration` CI job that
  installs a pinned `howlcreate` commit and asserts the real
  `howlcreate.engine.candidate_ingestion.develop_candidate` import succeeds before
  running `tests/test_end_to_end_ecosystem.py`, so this suite is now genuinely proven
  against the real module in addition to the existing in-repo fallback path. The
  equivalent gap on the HowlPlane side (installing `howldream` in HowlPlane's own CI)
  is tracked in `issues.md`, owned by that repo.
* See `docs/architecture.md` ("Verified status" note), `docs/ecosystem.md`
  (corrected integration table), and `README.md` (corrected adapter status table) for
  the full per-integration breakdown.

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

## Resilience and measurement hardening (2026-10-02)

- Added candidate exploration bridge, polymorphic validation, and chronology audit.
- Removed per-candidate embedded source duplication in exploration results.
- Separated requested/supported/applied sampling controls and observed model identity.
- Added WAKE ECHO and versioned separate measurement counts.
- Preserved sanitized provider error envelopes and failed HTTP/command telemetry.
- Restricted default exploration allowlist to mock; remote calls remain explicit.

- Ecosystem verification now pins Create checkpoint-finalist retention hardening.

- Pin provider-core nested response-shape recovery and the matching Create dependency in ecosystem CI.

## Discovery and validation integrity hardening

- Separate discovery generation from verification ledgers; preserve legacy experiments.
- Reject ineffective context/risk controls; carry constraints and optional diversity memory.
- Preserve IDEA lineage while adding advisory normalized-token clusters, echo and ranking.
- Keep subordinate citation failures at claim scope; preserve contradiction/critical gates.
- Classify validation provenance and audit exaggerated report claims without rewriting evidence.
- Support nested review claim IDs and document direct Dream-to-Create development.
- Export selected IDEA units as descendants with parent identity/span/hash and retained
  uncertainty; preserve parent rejection gates and reference scoped parent checks.
- Keep unverified tradeoff CONFLICT statements unresolved; only actual contradiction or
  critical failure triggers semantic rejection. Pin ecosystem CI to merged Create support.
