# Exposed Dream field audit

All structural request fields are validated by strict contracts, snapshotted in the
result or Experiment, and fail on unknown keys. Provenance is descriptive open metadata,
not executable configuration. Controls are revalidated at explore entry after mutation.

| Request field | Used / observable behavior | Persistence / rejection |
| --- | --- | --- |
| schema_version | selects strict request contract | validated constant |
| request_id | run objective/parent lineage | envelope/request provenance |
| parent_run_id | immutable descendant relationship | manifest/envelope |
| objective | all prompts, relevance, report | snapshot/envelope |
| originating_component | DAG and producer origin | envelope/provenance |
| requested_mode | dream/nightmare or paired perturbation setup | Experiment condition and perturbations; paired remains existing combined treatment |
| purpose | ledger hidden/exposed and generation task | snapshot/provenance |
| constraints | prompt guidance, preserved for Create hard gate | snapshot/candidate provenance; UNVERIFIED compliance scope |
| evidence_refs | WAKE ledger; generation only outside discovery | snapshot/result with provenance |
| context_refs | unsupported resolver | nonempty rejected UNSUPPORTED_CONTROL |
| risk_class | no arbitrary risk-policy engine | only EXPLORATORY accepted; otherwise UNSUPPORTED_CONTROL |
| authority | fail-closed advisory, executable=false | all handoffs |
| budget | bounded calls/candidates/trials/provider controls | snapshot + execution metadata |
| provider | strict ProviderConfig / explicit transport | manifest; truthful actual model metadata |
| source_candidates | development/review speculative context; never evidence | single canonical provenance plus hashed compact refs; explicit discovery rejects |
| provenance | descriptive audit inputs only | carried in request_provenance, never dispatched as commands |
| explored_families | compact area avoidance prompt | snapshot; no full prior text required |
| diversity_memory | experimental sibling labels added to later calls | snapshot/result treatment flag |
| ranking_criteria | explicit novelty/objective-fit advisory weights | snapshot/discovery.json ranking rationale |

Budget details: max_calls hard dispatch limit; max_candidates/trials bounded generated
counts; max_tokens is transported for supported HTTP providers (command unsupported,
reported); max_duration_seconds is per-call timeout, not whole-run duration;
provider_allowlist and local_only are restrictive gates; allow_local_inference ANDs
with provider opt-in; forbid_local_inference and environment prohibition override it.
No provider control is falsely marked applied. Raw command byte/time controls live in
reviewed command profile and execution metadata, not generated artifacts.

Experiment-only fields: name/run labeling; schema_version strict; objective/hypothesis
snapshot (hypothesis is descriptive experimental intent, not a generation control);
mode condition; provider transport; baseline/generation counts and requested sampling;
max_calls/trials/seed generation budget and execution sampling provenance;
evidence WAKE plus purpose-dependent prompt; context snapshotted relative files on
explicit Experiment read; speculative_candidates development unverified data;
perturbations explicit non-baseline treatment; retain_text removes text-derived records
and disables replay. Purpose/constraints/diversity/ranking behave as described above.
