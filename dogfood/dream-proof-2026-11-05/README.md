# Dream to Proof dogfood, 2026-11-05

Nine claims drawn from the November 2026 Ruby Renaissance archive
(`ruby_ideas/claude/11_sources.md`, `howl_evidence/rv_ruby_install.log`), run
HowlDream 0.4.5 (feat/dream-proof-bridge) -> HowlProof 0.2.0b1 (feat/research-claims-evaluator)
-> HowlDream. Offline: no network, no model, no browser. `inputs/` was written before the run
and is checksummed in `INPUT_SHA256SUMS` (verify with `cd inputs && sha256sum -c ../INPUT_SHA256SUMS`).
Fixtures were not edited to change a result.

Reproduce: `HOWLDREAM=<bin> HOWLPROOF=<bin> ./run.sh` (exact output in `run_output.txt`, artifacts in `outputs/`).

## Honest evidence provenance

The source facts are **transcribed from the archive's records**, which are tool summaries of
the pages; they were not re-fetched here. They are declared `DERIVED_FROM_EXTERNAL_DATA` and
independent of the implementation. So `SUPPORTED` below means "consistent with the archived
record of an independent source", not "freshly verified against the live source".

## Results

| Claim | Case | Result | Defensible? |
| --- | --- | --- | --- |
| rr-1 Ruby took 73.1 s | accurate, primary-source evidence | SUPPORTED | yes, matches archived S2 |
| rr-2 Python took 40 s | inaccurate | REFUTED | yes, S2 says 74.6 s |
| rr-3 Ruby ~40% cheaper than TypeScript | quantitative, no methodology/check | INCONCLUSIVE | yes; a citation is not a check |
| rr-4 cost $0.36 per run | currency | SUPPORTED | yes; `$` vs `%` would have been refused |
| rr-5 TIOBE top 10 by 2028 | speculative forecast | REQUIRES_EXTERNAL_VALIDATION | yes |
| rr-6a 186.6 / 73.1 = 2.55x | executable (arithmetic) | SUPPORTED | yes, deterministic; inputs come from the claim |
| rr-6b rv installs Ruby < 30 s | needs execution; only agent-run log | INCONCLUSIVE | yes; the 2.010 s log is not independent evidence |
| rr-7 Ruby in TIOBE top 20 | contradicted by newer source | INCONCLUSIVE, conflict recorded (`newer: S5-tiobe-sep`) | yes; newer is not proof |
| rr-8 YJIT 92% faster per Ruby 4.0 notes | source exists, does not address the claim | INCONCLUSIVE (`irrelevant`) | yes |

Totals: 3 supported, 1 refuted, 4 inconclusive, 1 requires external validation, 0 errors,
0 tooling failures. Candidate disposition: `INVESTIGATE` (LOW); HowlProof verdict
`INSUFFICIENT_EVIDENCE` (`no_acceptance_criteria`), exit code 40, because no operator
acceptance contract was supplied and none was invented. Candidate status `IMPORTED`,
authorship `EXTERNAL_AUTHORED`, IDs and evidence digests survive in `outputs/assessment.json`.

## Operational notes

Single process at a time, no browser, no inference; each stage under a second. Memory was
15 GB of 24 GB used by other processes before and after. The claims were authored as
structured claims with checks by hand (`run.sh` step 2); that manual translation is the
limit of what the bridge automates today.
