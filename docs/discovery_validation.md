# Discovery and validation integrity

Experiment `purpose` is separate from `mode` (dream/nightmare). `discovery` withholds
the entire evidence ledger from all generation prompts, including the conventional
control. It retains the ledger in the snapshot for claim-level WAKE. A fresh
`howl.exploration/v1` request defaults to discovery. Subject and objective remain
visible; keep detailed facts out of objective text if you want minimal anchoring.

`development` exposes practical context and selected opportunities. Requests with
`source_candidates` and no explicit purpose default to development for compatibility.
`verification` exposes the ledger and requests falsification. `review` is deterministic
claim checking without model calls. Legacy `Experiment` files default to development,
so old evidence-based benchmarks retain their intended context. Explicit discovery
with selected source-candidate text is rejected: use compact `explored_families`.

```json
{
  "schema_version": "howl.exploration/v1",
  "request_id": "subject-only",
  "objective": "Find meaningful software opportunities for an MLB team.",
  "purpose": "discovery",
  "constraints": ["No private player tracking"],
  "diversity_memory": true,
  "explored_families": ["bullpen fatigue", "ticketing"],
  "ranking_criteria": ["novelty", "objective_fit"]
}
```

Constraints are prompt guidance and preserved in candidate provenance as
`hard_constraints`, never advertised as verified compliance. Create imports them
into its hard-constraint gate. `context_refs` has no safe resolver and is rejected
with `UNSUPPORTED_CONTROL`; attach snapshotted `evidence_refs`. Arbitrary risk
policies are unsupported; only `EXPLORATORY` is accepted. Unknown fields fail schema
validation. Budget timeout is per request, not total-run wall time. Command sampling
and token ceilings remain explicitly unsupported controls; transport limits differ.

With `diversity_memory`, later experimental calls receive compact normalized labels
from prior IDEA lines, never the full texts or evidence ledger. The baseline receives
only externally supplied family memory. This is a declared treatment, not an
independently sampled comparison. Continue with the run's `discovery.json` family
labels. It is advisory: avoiding an explored family must not override safety/utility.

`discovery.json` records each IDEA line with immutable candidate identity, character
span, source-text SHA-256, cluster, similar-to link and representative. Original text
and duplicates remain intact. Aggregate ratios in `metrics.json` use normalized
content-token overlap, a small synonym map, and leading content phrase links, not
calibrated semantic similarity. Phrase links may over-cluster distinct mechanisms;
inspect representatives and keep the raw units. This heuristic was revised after a
remote smoke exposed long-paraphrase false negatives.
The report labels their scope and emits advisory `DISCOVERY_ANCHORING_HIGH` at high
context coverage. Optional equal-weight ranking uses only explicitly supplied
`novelty`/`objective_fit` criteria; neither proves usefulness or grants authority.

## Evidence provenance

Each Evidence/EvidenceRef may carry `provenance`: `source_type`, `produced_by`,
`source_ref`, `independent_of_implementation`, `represents_observed_reality`.
Source types: EXTERNAL_GROUND_TRUTH, EXTERNAL_OBSERVATION, HISTORICAL_DATASET,
DERIVED_FROM_EXTERNAL_DATA, MODEL_INVARIANT, SYNTHETIC_FIXTURE, OPERATOR_EXPECTATION,
SIMULATION_EXPECTATION, MODEL_SELF_CONSISTENCY, or conservative UNCLASSIFIED.
External declarations require producer and reference; ground truth also requires
independent observed data. Self-authored fixtures/expectations cannot declare observed
reality. These are declarations, not authenticated data. WAKE carries the provenance
and names its limited scope: citation presence, ledger consistency, or arithmetic
self-consistency. It never promotes expectation types to ground truth.

Citation/unsupported subordinate defects remain claim-level diagnostics. Triage may
still INVESTIGATE a useful proposal with such defects. Contradictions and explicitly
critical failed claims remain blocking; hard safety/authority gates are unchanged.
Structured nested review claims inherit missing IDs but mismatched identities fail.

## Validation results and product-report audit

`howldream.evidence.ValidationResult` records expected-value origin, source provenance,
artifact reference, test scope, outcome and optional study-design declarations.
`maturity()` derives levels: 0 untested/unclassified; 1 controlled checks; 2 observed
retrospective dataset; 3 independent benchmark; 4 prospective operational evaluation.
A level is scoped to one result and based on declarations, not universal readiness.
A passing synthetic fixture supports "Passed controlled synthetic validation".
Self-consistency supports model-assumption consistency, not external accuracy.
Historical data supports retrospective findings, not causal improvement in wins.

```bash
howldream audit-report product-report.md --validation report-evidence.json
```

The ledger uses `validations` and exact-sentence `bindings` (`claim`, `validation_ids`).
Sensitive empirical/absolute language without appropriate bound passing evidence emits
`CLAIM_EVIDENCE_MISMATCH`, supporting records, types, insufficiency and narrower wording.
Exit 1 means findings; output is advisory. Original report and evidence stay untouched.
This heuristic cannot validate entailment, authenticate references, or detect every
paraphrase. Human review remains necessary even with no findings. The generated Dream
report also receives an audit; its fixture/scope limitations are explicit.

`validation_requirements()` provides prototype-level checklists for decisions,
forecasts, detectors and simulations. No prototype must meet production standards,
but it must report the validation actually performed.

## Direct Dream to Create

Export a typed candidate using `howldream export RUN --candidate-id ID`, then use
`howlcreate scaffold --from-dream candidate.json` for offline plans,
`howlcreate develop --from-dream candidate.json --provider command --command-config PROFILE`,
or `howlcreate explore --from-dream candidate.json --provider deterministic --max-calls 8`.
Explicit selection means development only; it is not a verification endorsement.
Source identity, claims, uncertainty, evidence needs and provenance survive. Contradicted
or rejected sources require review. Outputs remain advisory with no execution authority.

Use an IDEA unit ID from `discovery.json` as `export --candidate-id` to select one
opportunity instead of the entire multi-idea response. The descendant carries parent
candidate identity, source span/hash and cluster, retains batch uncertainty/constraints
with an explicit association limit, and keeps parent rejection/contradiction gates.
Parent verification results are referenced rather than relabeled as checks of the unit.

For remote command comparisons, isolate the CLI's project/global instructions and
skills, use an explicitly reviewed neutral context, and record effective prompt scope.
A CLI can load ambient context outside Dream's serialized prompt; Dream's echo metrics
cannot measure unseen context. The directed smoke detected this and reran in Claude
safe-mode with tools disabled, neutral cwd and a neutral explicit system prompt.

A `CONFLICT:` tradeoff or concern is an unresolved review item unless checks establish
an actual contradiction in the candidate's assertion. It does not automatically reject
an otherwise useful opportunity. Source artifacts predating this repair retain their
original statuses; selection does not silently rewrite historical rejection evidence.
