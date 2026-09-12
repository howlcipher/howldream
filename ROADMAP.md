# Roadmap

## Phase 1: Controlled Divergence

Experiments, baseline/control, mock and real providers, perturbations, artifact
snapshots, claim grammar, scoped WAKE checks, scoring, duplicates, replay, reports,
balanced deterministic fixtures, and dogfood. Experimental, not production-ready.

## Phase 2: Reliability Lab

Completed measurement foundation: versioned split-aware DreamBench, claim coverage,
binary and category metrics, DreamValue calibration, fair budgets, conceptual
clusters, curves, blind review packets, canonical artifacts, and research reporting.
Decision at the time: HOLD (held-out extraction failed and independent value ratings
were pending). Superseded by Phase 3, below, which closed both gaps in 0.3.0/0.3.1 —
this HOLD is historical, not the current status.

## Phase 3: Local Model Instrumentation — completed (0.3.0 / 0.3.1)

Collected 84 independently authored natural-language cases (DreamBench 0.3.0) and ran
blinded multi-rater value judgments and equal-budget live Ollama baseline/DREAM
comparisons across 10 systems-engineering tasks. The 0.3.1 evidence-integrity audit
reconciled and partly withdrew the initial 0.3.0 claims (raters reclassified as
simulated personas, a zero-denominator multiplicative ratio withdrawn, promotion
downgraded to PROMOTE WITH CONDITIONS pending real human review). See
`change_log.md` and `docs/milestone_three_report.md`. Hosted private reasoning
remains outside the contract.

## Phase 4: Ecosystem Intelligence — partially real (0.4.0 / 0.4.1)

**Corrected 2026-09-11**: the original 0.4.0 entry claimed this phase as "validated."
Actual status per adapter (see `docs/ecosystem.md` for detail): HowlCreate's
`candidate_ingestion` import and HowlPlane's exploration-policy runner are real,
merged code, but neither is exercised via a real cross-repo import in either
repo's CI — both are CI-unverified, not validated. The HowlFrame verifier program
is not yet merged anywhere (unmerged howlframe branch only) — "bounded HowlFrame
verifier programs" is not yet true. HowlRelay continuation is real, merged, and
genuinely validated end-to-end. Preserve authority boundaries at every adapter
regardless of merge/CI status.

## Phase 5: Learning from Dreams

Analyze experiment history: prompt/failure patterns, provider differences, perturbation
sensitivity, verifier coverage, and candidate survival. These are research questions,
not current supported conclusions or autonomous self-improvement.
