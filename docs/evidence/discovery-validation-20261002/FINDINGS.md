# Findings and repair decisions

Historical evidence directory: `howl-creative-dogfood/run04_cubs_baseball/`.
Subdirectories: `cubs-mlb--claude-opus-5-5--20261002T143915Z-459773e2` (C),
`wrigleysentry--antigravity-flash-gemini38--20261002T144500Z-a3f18b29` (W),
`baseball-open--codex-gpt6--20261002T145125Z-8adbe94b` (B).
Live reproductions: reproduction-baseline.json plus tests cited below. No original
product/evidence is edited. CONFIRMED describes a demonstrated interface/code gap,
not proof of model-level creative superiority.

| Finding | Dogfood evidence | Current reproduction | Classification | Root cause | Component | Repair decision | Regression test |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 Discovery/evidence separation | C HD-A and ledger/no-ledger runs | ledger text in all prompts | CONFIRMED | same evidence serialized for generation and WAKE | Dream engine/schema | explicit purpose; discovery withholds ledger | test_discovery_ledger_is_verification_only |
| 2 Source taxonomy | W evaluation.py manually declares expected_carry_shift_ft; labels historical | Evidence fields only id/text/facts | CONFIRMED | no expected-value provenance | Dream evidence/schema | typed provenance, conservative UNCLASSIFIED | test_validation_provenance_is_preserved |
| 3 Evidence-compatible language | W AFTER_ACTION_REPORT calls prototype production-grade and historically tested | no report audit API/CLI | CONFIRMED | report assertions unbound to validation artifacts | Dream evidence/CLI | advisory exact-binding claim audit | test_exaggerated_report_claim_flagged |
| 4 Echo concentration | C repeated ledger-derived Wrigley/rule ideas | existing exact/near sentence echo only; no candidate context concentration | PARTIALLY_CONFIRMED | claim echo not exploration anchoring metric | Dream discovery | normalized-token advisory coverage ratios/warnings | test_cluster_paraphrase_lineage_and_echo |
| 5 Declared controls | C HD-C | constraints/context/risk omitted in stored prompts; reproduction JSON | CONFIRMED | request fields discarded when building Experiment | Dream contracts/engine | constraints prompt+handoff; reject unresolved refs/arbitrary risk | test_ineffective_controls_rejected; test_mutated_unsupported_control_revalidated |
| 6 Whole-candidate citation failure | C HD-B | useful candidate plus one missing citation becomes REJECT | CONFIRMED | all claim classifications treated as candidate failure | Dream scoring | citation/unknown subordinate defects diagnostic; contradictions/critical gates remain | test_claim_level_mixed_wake_and_critical_gate |
| 7 Continuation diversity | B HD1; C HD-A | candidate index only; no sibling family memory | CONFIRMED | independent calls lack compact explored families | Dream generation | optional compact families, declared treatment | test_diversity_memory_prompt_not_full_text |
| 8 Clustering/dedup/ranking | C HD-H; B HD2 | lexical whole-response grouping exists; no IDEA units/ranking | PARTIALLY_CONFIRMED | batch identity and rudimentary dedup already implemented | Dream discovery | IDEA spans/hashes, transparent clusters, representatives, optional advisory rank | test_cluster_paraphrase_lineage_and_echo |
| 9 Dream to Create | C HC-6 | typed assessed develop/scaffold already exist; no direct selected-candidate explore | PARTIALLY_CONFIRMED | reverse ingestion requires assessment/manual problem conversion | Create CLI/pipeline | --from-dream selection; preserve source once plus refs | test_direct_dream_scaffold_preserves_entire_source; test_dream_source_passed_into_creative_operators |
| 10 Budget convergence | W max-calls8 findings | fixture uses 8 optional-stage calls; no synthesis/finalists | CONFIRMED | global budget lacks downstream reservation | Create pipeline | reserve including repair, skip optional, explicit bounded evaluation subset | test_reserved_synthesis_and_convergence; test_budget_excess_output_preserves_deferred_nodes |
| 11 Conventional winner | C HC-3 | five independent dimensions and novelty wildcard already exist; operator priors absent | PARTIALLY_CONFIRMED | scalar balance cannot preserve every useful dimension leader | Create convergence | preserve eligible-only leader portfolio; do not change weights from one case | test_novelty_leader_survives_balanced_ranking_and_gates |
| 12 External requirements | W empirical carry claim; B correctly labels synthetic vs data | no product-kind validation checklist/maturity contract | CONFIRMED | generic WAKE scope not product empirical evaluation | Dream evidence | explicit levels and prototype checklists | test_product_validation_checklists; test_operator_expected_value_is_not_ground_truth |
| 13 Final product claim audit | W report exaggerated absolute language | no binding/strength audit | CONFIRMED | reports assume test pass means reality | Dream evidence | CLI flags without rewriting original | test_audit_report_cli |

Additional dogfood reports: polymorphic validate rejects exploration contracts is
ALREADY_FIXED (baseline test_polymorphic_validation passes). Missing nested claim
candidate IDs is CONFIRMED in review's direct verify dictionary access; descendants
now inherit absent IDs and reject conflicting IDs. Generic WAKE is not an independent
baseball physics verifier: DIFFERENT_ROOT_CAUSE, scope limitation; no physics oracle
or model-based factual truth engine is introduced. Unsupported command sampling is
ALREADY_FIXED and honestly reported; no transport change needed. Provider metadata,
local prohibition, structured CLI adapters and resilience passed baseline tests.

No model-level improvement is inferred from authored fixture output. Remote comparison
is one behavior check, not a statistical superiority study. No general ecosystem rewrite.

## New smoke finding: unverified CONFLICT statements rejected entire candidates

Finding: conceptual tradeoffs and evidence-quality concerns were treated as candidate
contradictions solely because the model used CONFLICT prefix.
Dogfood evidence: not asserted from the baseball run; new directed smoke evidence.
Current reproduction: final A candidate 0 says standardization_vs_autonomy, with no
CONTRADICTED checks, yet original envelope marks REJECTED. B candidates correctly
question the authored ledger's provenance but are also marked REJECTED.
Classification: CONFIRMED.
Root cause: explore initialized cand_contradictions from every CONFLICT claim before
checking scoped WAKE results.
Affected component: Dream candidate summary, not provider-core.
Repair decision: only actual CONTRADICTED checks/critical failures gate rejection;
unverified tradeoffs remain unresolved issues. Correct identification of conflicting
ledger evidence does not itself contradict a candidate's assertion.
Regression test: test_unverified_tradeoff_is_not_a_candidate_contradiction.
Original smoke envelopes remain unchanged. Direct handoff chooses a non-rejected
source candidate, retaining the old rejection gates rather than rewriting evidence.
