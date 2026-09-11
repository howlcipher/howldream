# DreamBench and DreamValue

## DreamBench

DreamBench 0.2.0 has 156 authored, template-derived natural-language cases and
312 claim annotations. Development is the default to reduce accidental leakage.

```bash
howldream benchmark list
howldream benchmark run dreambench --split development
howldream benchmark run dreambench --split held_out
howldream benchmark report .howldream/benchmarks/dreambench_0.2.0_held_out.json
```

Splits are 65 development, 26 validation, 39 held-out, and 26 confirmation cases.
Held-out execution is explicit and recorded. An early pre-publication dry run
informed a fixture correction, so confirmation was created and run once after
detector logic froze. Published definitions are immutable; corrections require a
new version.

Each case records provenance, expected behavior, deterministic-check availability,
difficulty, severity, split, notes, and claim-level ground truth. The matrix covers
all 13 requested failure categories and paired grounded controls. Cases contain
prose, multiple claims, mixed content, and deliberately difficult boundaries.

Output includes claim and case predictions, TP/FP/TN/FN, precision, recall, F1,
specificity, error rates, category summaries, claim coverage, scorer metadata,
dataset hash, code SHA, exclusions, and timestamps. Undefined zero-denominator
metrics remain null. JSON and Markdown reports are generated together.

Sentence extraction and annotation matching are lexical heuristics. Verification
is limited to supplied-ledger consistency, source-ID presence, and exact arithmetic.
Missing claims are visible and cause false negatives. UNRESOLVED never means FALSE.

## DreamValue

DreamValue 0.1.0 contains 24 technical tasks with equal 10-candidate baseline and
DREAM calibration pools. Run `howldream evaluate dreamvalue`.

It reports lexical diversity, authored conceptual clusters, duplicates,
irrelevance, unsupported and contradicted candidates, INVESTIGATE and
verification-survival rates, divergence and candidate-count curves, and Verified
Novel Candidate Yield. VNCY requires a unique approach, relevance, no labeled
unsupported or contradicted assumption, and INVESTIGATE or
SURVIVES_VERIFICATION.

Approach and outcome labels are human-authored. The generated blind packet omits
condition labels and supports independent reviewers. Calibration results test
metric behavior; they do not show that live DREAM beats repeated sampling.

## Reproduction and policy

CI runs the development smoke suite, metric tests, package validation, and all
Milestone One checks without a live provider. The Manual evaluation workflow runs
all deterministic splits and uploads artifacts. Live evaluation runs locally with
an explicitly configured provider and preserves settings, outputs, usage, latency,
and limitations.

Checked-in files under `evaluation/results/` are canonical measured results.
`scripts/build_site_evaluation.py` derives `docs/evaluation.json` from them.
