# Experiment format and CLI

YAML and JSON inputs share strict schema version 1. Unknown properties, invalid types,
duplicate evidence IDs, excessive budgets, and unsupported versions fail validation.
Run `howldream validate examples/self_detection.yaml` before generation.

| Field | Meaning |
| --- | --- |
| schema_version | Required integer 1 |
| name / objective | Required identifier and question |
| hypothesis | Optional expected outcome |
| mode | dream (default) or nightmare |
| baseline | candidates 1–100, temperature 0–2; defaults 3 and 0.2 |
| generation | candidates 1–100, temperature 0–2; defaults 6 and 1.2 |
| trials / seed | 1–20 trials and base seed; total requests limited to 500 |
| provider | kind, model, base_url, allow_remote, timeout_seconds, max_tokens |
| evidence | Unique source IDs with text and string key/value facts |
| context | File paths relative to experiment file, snapshotted at load time |
| perturbations | Ordered omit_context, reverse_context, false_premise, contradict_context |
| retain_text | Defaults true; false suppresses content retention and replay |

`omit_context` retains the first half of evidence records (rounded down);
`reverse_context` reverses record order. False-premise and contradictory-context
operators append explicitly labeled untrusted text supplied in their `text` field.
They never modify the authoritative original ledger used by WAKE. Baseline runs first
in each trial. Prompt framing and sampling both change in the default DREAM comparison;
it is a condition comparison, not an isolated temperature causal estimate.

## Commands

```bash
howldream --help
howldream --version
howldream validate examples/self_detection.yaml
howldream run examples/self_detection.yaml --output .howldream/runs
howldream dream examples/self_detection.yaml
howldream nightmare examples/nightmare.yaml
howldream wake .howldream/runs/hd-REPLACE_WITH_RUN_ID
howldream inspect .howldream/runs/hd-REPLACE_WITH_RUN_ID
howldream replay .howldream/runs/hd-REPLACE_WITH_RUN_ID
howldream compare .howldream/runs/hd-FIRST .howldream/runs/hd-SECOND
howldream report .howldream/runs/hd-REPLACE_WITH_RUN_ID
howldream benchmark list
howldream benchmark run dreambench --split development
howldream benchmark run dreambench --split held_out
howldream benchmark report .howldream/benchmarks/dreambench_0.2.0_held_out.json
howldream evaluate dreamvalue --output .howldream/evaluations
```

`run` executes baseline, generation, and WAKE. `dream` and `nightmare` establish a
baseline and save unverified generation for a later `wake`. `wake` reads retained
outputs without calling the provider and writes a new run. `replay` generates again
from the stored snapshot and creates a lineage link. `compare` returns each run's
baseline and experimental metrics. Paths are explicit; run IDs are not globally resolved.
Benchmark development is the default. Held-out and confirmation execution require
an explicit split and record that fact in the artifact. DreamValue writes its
machine-readable result and a blinded human-review packet.

## Claim grammar

Model output remains stored as observed. One proposition per line is requested:
`IDEA: proposal`, `ASSUMPTION: prerequisite`, `FACT: key=value`, `PREMISE: key=value`,
`DRIFT: key=value`, `CITE: source_id`, `CALC: 17 * 19 = 323`, `UNKNOWN: key`,
`CONFLICT: key`. Unrecognized lines become PROSE with unresolved status. This grammar
is a narrow extraction seam, not natural-language entailment. A proposal label is
not evidence, nor can it grant permission. Operators author the evidence ledger;
generated text never adds facts to it.

## Reproducibility

Mock output replay is exact only for the same fixture implementation and unchanged
retained inputs; run IDs, timestamps, and durations differ. Real providers offer
configuration replay only, even with seeds. Model names may be mutable; model version
is null when not exposed. Redaction or disabled text retention can prevent replay.
Trials are recorded separately as well as pooled. This version does not estimate
confidence intervals or control run-order effects.

Remote replay requires `--allow-remote` in the current CLI invocation after you
review the stored endpoint and inputs. A stored flag is not fresh authorization.
Exact mock replay rejects a different implementation hash. WAKE records current
analysis implementation/version/commit separately from generation provenance.
