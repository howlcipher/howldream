# Bounded remote subject smoke

Subject only: Find meaningful software opportunities for a developer platform team.
Model reported by every call: claude-sonnet-5-5. Provider reported: claude; transport:
operator-reviewed remote command, claude-json adapter. Authenticated existing Claude
session; no local model, provider fallback, tools or product build. No MLB remote run.

Final isolated profile uses --safe-mode, a neutral explicit system prompt, empty tools,
strict MCP config and no session persistence; neutral cwd. It avoids ambient CLAUDE.md,
skill/plugin/rule context found during the initial diagnostic comparison.

| Condition | Calls | Native experimental candidates | IDEA units | Input (uncached + creation + read) | Output tokens | CLI-reported USD estimate | Wall seconds |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| A subject-only discovery | 3 | 2 | 18 | 6 + 2595 + 0 | 4372 | 0.054112 | 43.9746 |
| B authored ledger exposed in development | 3 | 2 | 10 | 6 + 3150 + 0 | 3212 | 0.044732 | 33.2869 |

Final combined reported estimate: $0.098844; 13,341 total input/cache/output tokens;
77.2615 seconds. Each condition includes one additional conventional baseline response.
Dollar values are Claude CLI-reported estimates, not independently audited billing.
Requested output limit 768 tokens and sampling are unsupported by this command transport;
actual usage is reported rather than pretending enforcement. Timeout 120 seconds per call.
No transport redesign or unsupported-control masking.

Initial diagnostic comparison (preserved): 6 calls, $0.2647572 CLI-reported estimate,
57,990 total tokens, 77.3191 seconds. Ambient context and lexical false negatives were
identified. Total mission remote inference: 12 calls, $0.3636012 reported estimate,
71,331 tokens. Initial summary's started_at field was incorrectly recorded after execution;
use immutable run manifests for actual start timestamps. Final summary fixes the field.

Both final generation runs completed without provider failures. Scoped uncertain claims:
49 A, 40 B; no contradicted checks. No unknown factual assertion became accepted truth.
One A and both B envelopes were originally marked REJECTED because unverified CONFLICT
tradeoff/provenance concerns were treated as contradictions; the smoke exposed this bug.
It is fixed with deterministic regression coverage; originals are preserved, not relabeled.
The actual handoff chooses the non-rejected A source's unit 11 and retains all uncertainty.

Generated-output analysis was revised offline (WAKE descendant, v3) after observed
false-positive family links. Final proxy clusters: A 16/B 6; context echo A 0/B .8;
repeated-family proxy A .1111/B .4. Inspect remote-smoke-analysis-v3.json and
family-review-final.json (manual broad families A14/B5). Neither method measures
statistical superiority, feasibility, or observed product value.

Review adds the operator-authored ledger only after A generation, retaining the complete
source candidate in remote-final-candidate-reviewed.json. No fact retrieval or historical
validation is claimed. Source classification remains OPERATOR_EXPECTATION. Direct export
selects one IDEA with span/hash/parent identity and preserves scope limitations.

Artifacts: final profile; remote-smoke-final-summary.json; raw immutable remote-runs;
offline-review-runs; v3 analysis; selected-dream-unit.json; dream-create-cli-scaffold.json;
initial summaries and logs. No secrets stored. LOCAL_LLM_USED: NO.
