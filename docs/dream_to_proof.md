# Dream to Proof

HowlDream proposes; HowlProof challenges. Neither manufactures certainty.

```bash
howldream export-proof candidate.json --evidence evidence.json --out bundle/
howlproof evaluate bundle/ --profile research --evidence-root proof-out/ --json > result.json
howldream import-proof --bundle bundle/ --result result.json --out assessment.json
```

Requires HowlProof with the `research.claims` evaluator (the `research` profile). The
bridge is offline: no network, no model call, no generated code is run. It invents no
acceptance requirement; with no operator contract HowlProof's verdict stays
`INSUFFICIENT_EVIDENCE` and the per-claim results are the substantive output.

## Export

`export-proof` validates a `howl.candidate/v1`, then writes `claims.json`
(`howl.claim_bundle/v1`) and hashed evidence files. It preserves candidate and claim
IDs and claim text, and records:

* `authorship.kind`: `EXTERNAL_AUTHORED`, `MODEL_GENERATED` (with provider and model),
  `MOCK`, `SYNTHETIC_FIXTURE` or `UNKNOWN` (legacy). Externally authored candidates
  export with status `IMPORTED`, never `GENERATED`.
* a claim `category`: `EMPIRICAL`, `TECHNICAL`, `HYPOTHESIS`, `VALUE_JUDGMENT`. An explicit
  `category` on a structured claim wins; otherwise a conservative heuristic labels it
  (`category_basis`) and defaults to `HYPOTHESIS`. Forecast and judgment wording becomes
  `VALUE_JUDGMENT`.
* a `PROPOSED`, ungrounded `verification_plan`. A `check` exists only if the claim's author
  supplied one (`fact_compare` or `arithmetic`; see HowlProof's `docs/research_claims.md`).
* evidence trust: `independent` is true only for external source types declared independent
  of the implementation. Agent-supplied evidence stays non-independent and cannot support
  a claim. `facts.published_at` / `facts.retrieved_at` become the evidence timestamp.

The output directory must be empty. Re-exporting the same candidate is byte-identical.

## Import

`import-proof` checks the result was produced for this exact bundle (digest), then emits a
`howl.assessment/v1` whose `evidence` holds one `proof_claim_result` per claim (status,
method, explanation, evidence considered with trust, conflicts, what was not checked) and
whose `provenance` records the Proof run, version, verdict and timestamps. Original
candidate and bundle are never modified.

| Claim results | Disposition |
| --- | --- |
| all SUPPORTED, integrity passed | `ACCEPT_FOR_DEVELOPMENT` (MEDIUM) |
| all REFUTED | `REJECT` (HIGH) |
| some REFUTED, rest anything | `INVESTIGATE` (LOW) |
| otherwise (INCONCLUSIVE, REQUIRES_EXTERNAL_VALIDATION, ERROR, not assessed) | `UNRESOLVED` (LOW) |

INCONCLUSIVE is never turned into REJECT or acceptance, and one claim never decides
another. Importing the same result twice yields the same assessment.

## Real discovery without local inference

`explore --command-config profile.json --allow-remote` (the `command` provider) already
lets an authorized external agent author candidates under a bounded budget, and
`cluster --external` records ideas written elsewhere as `CLUSTERED`. Neither is changed;
no provider adapters were added. The default `mock` provider is labelled `MOCK` in
exports. Local inference remains off.

## Compatibility

* HowlDream 0.4.5 (this change adds `IMPORTED` to the candidate status enum; old
  artifacts with `GENERATED` still validate).
* HowlProof 0.2.0b1 with `research.claims` v1.
* Candidate-schema errors from `review` and `export-proof` now name `howl.candidate/v1`
  and list the accepted values.

## Known limits

Natural-language extraction still returns a compound sentence as one claim; split compound
claims and author checks when a claim should be decided. Nothing here fetches or verifies a
URL. See the dogfood record in `dogfood/dream-proof-2026-11-05/`.
