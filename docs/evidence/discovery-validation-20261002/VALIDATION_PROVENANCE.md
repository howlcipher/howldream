# Validation provenance

Typed examples in demonstrations.json are authored taxonomy demonstrations, not actual
external benchmarks. Source declarations cannot authenticate a purported external record.

| Type | Expected-value origin | Independence/reality | Compatible claim |
| --- | --- | --- | --- |
| EXTERNAL_GROUND_TRUTH | independent observed record, with source reference and producer | both required explicitly | scoped agreement with referenced observations, after real checking |
| HISTORICAL_DATASET | recorded historical observations | declared; causal benefit not inferred | retrospective evaluation found X |
| SYNTHETIC_FIXTURE | generated/manual controlled test case | no observed-reality declaration permitted | passed controlled synthetic validation |
| OPERATOR_EXPECTATION | developer/user authored expected answer | cannot imply observed reality | matches operator-authored expectation |
| MODEL_SELF_CONSISTENCY | implementation/model assumptions | no external accuracy credit | consistent with stated model assumptions |

Additional types: EXTERNAL_OBSERVATION, DERIVED_FROM_EXTERNAL_DATA,
MODEL_INVARIANT, SIMULATION_EXPECTATION, conservative UNCLASSIFIED.
Each ValidationResult declares expected origin, producer/ref, artifact, scope, outcome,
study controls, metrics and limitations. Maturity derives from those declarations:
0 untested/unclassified, 1 controlled checks, 2 observed retrospective data,
3 independent external benchmark, 4 prospective operational evaluation.
No universal "validated" endorsement follows from a level.

Manual Wrigley carry values have no independently observed source in the inspected
validator. Their proper source class is OPERATOR_EXPECTATION, not automatically
EXTERNAL_GROUND_TRUTH or historical observed outcomes. Original artifacts remain unchanged.
A descendant audit flags original exaggerated product wording.

Decision tools need independent outcomes and counterfactual limits; forecasts need
holdout/error/benchmark data; detectors need positives/negatives/controls/population;
simulations need independent measurement/calibration. Prototype requirements are
explicit scope checklists, not impossible production gates.

Report audits use explicit exact-sentence evidence bindings, scoped PASS results,
provenance/design requirements and narrower suggestions. Sensitive absolute language
requires scoped human review. They neither fetch referenced URLs nor independently
prove entailment; an apparently valid declaration can still be dishonest. Do not use
an audit with zero findings as a truth certificate.
