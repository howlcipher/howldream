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
  `independent`, `source_type` and `represents_observed_reality` are **declarations**; Proof
  keeps them as claimed provenance and they confer no authority (see below).
* optional trust fields, validated and passed through, never invented: per claim
  `subject_terms` (terms a source must contain to be relevant), `checked_proposition` (the
  exact proposition checked) and `scope` (`{artifact, extent}`); per evidence `acquisition`
  (`{id, content_sha256}`, a pointer into a HowlProof acquisition store) and
  `methodology_quote`.

The output directory must be empty. Re-exporting the same candidate is byte-identical.

## Import

`import-proof` checks the result was produced for this exact bundle (digest), then emits a
`howl.assessment/v1` whose `evidence` holds one `proof_claim_result` per claim (status,
method, explanation, evidence considered with trust, conflicts, what was not checked) and
whose `provenance` records the Proof run, version, verdict and timestamps. Original
candidate and bundle are never modified.

| Claim results | Disposition |
| --- | --- |
| all SUPPORTED, integrity passed, every claim source-verified or deterministic | `INVESTIGATE` (MEDIUM) |
| all SUPPORTED, but some only against unverified, synthetic or unattributed evidence | `UNRESOLVED` (LOW) |
| all REFUTED, none scope-limited | `REJECT` (HIGH) |
| some REFUTED, or all REFUTED but some only within a limited scope | `INVESTIGATE` (LOW) |
| otherwise (INCONCLUSIVE, REQUIRES_EXTERNAL_VALIDATION, ERROR, not assessed) | `UNRESOLVED` (LOW) |

**`import-proof` never emits `ACCEPT_FOR_DEVELOPMENT`.** That value is a downstream trigger:
HowlPlane promotes a candidate to a HowlCreate development run when it sees it
(`howldream_runner.py`), so a research result must not be able to produce it. This is a
change from 0.4.5, where all-SUPPORTED produced it; the enum is unchanged for
compatibility. A fully supported bundle becomes `INVESTIGATE`, and the assessment carries a
`proof_evidence_summary` row with `evidence_status` (`ALL_CLAIMS_SOURCE_VERIFIED`,
`PARTIALLY_VERIFIED`, `UNVERIFIED`) and `development_approval: NOT_GRANTED`. Building,
deploying, purchasing or publishing needs a separate explicit approval that this tool does not
model. (The unrelated local `review` path can still emit `ACCEPT_FOR_DEVELOPMENT` from
Dream's own invariant checks; it is not fed by Proof and is unchanged.)

INCONCLUSIVE is never turned into REJECT or acceptance, and one claim never decides
another. A refutation that Proof marks `scope_limited` (for example "this README does not
mention X") is never turned into a rejection of the candidate: the broader question was not
evaluated. A SUPPORTED result without Proof's `assurance` record (a pre-M2 HowlProof) counts as
unverified. Each `proof_claim_result` row also carries `assurance`, `check_outcome`,
`checked_proposition`, `scope`, `scope_limited`, `broader_question` and `also_found_in` when
Proof supplied them. Importing the same result twice yields the same assessment.

## What "verified" means here

Proof separates *the check passed*, *bytes are intact*, *the source was observed being
acquired*, *the source is structurally relevant*, *a methodology is quoted*, *copies are not
corroboration* and *real-world truth*. Only an acquired source (`howlproof acquire`, passed to
`evaluate --acquisition-store`) can carry a sourced claim to SUPPORTED/REFUTED. A fabricated
number that matches its own check, a placeholder URL such as `example.org`, or an AI summary
yields INCONCLUSIVE with `check_outcome` recording what the numbers said. See HowlProof's
`docs/research_claims.md` for the full table.

## Real discovery without local inference

`explore --command-config profile.json --allow-remote` (the `command` provider) already
lets an authorized external agent author candidates under a bounded budget, and
`cluster --external` records ideas written elsewhere as `CLUSTERED`. Neither is changed;
no provider adapters were added. The default `mock` provider is labelled `MOCK` in
exports. Local inference remains off.

## Compatibility

* HowlDream 0.4.5 (this change adds `IMPORTED` to the candidate status enum; old
  artifacts with `GENERATED` still validate). M2 adds optional `acquisition` and
  `methodology_quote` to evidence input and optional claim trust fields; old inputs still work.
* HowlProof 0.2.0b1 with `research.claims` v1. **M2 requires the HowlProof evidence-trust
  release** (`assurance`, `howlproof acquire`) to reach SUPPORTED on real-world claims; with an
  older HowlProof every real-world SUPPORTED is read as unverified. Migrate by re-evaluating:
  old assessments are not rewritten.
* Candidate-schema errors from `review` and `export-proof` now name `howl.candidate/v1`
  and list the accepted values.

## Known limits

Natural-language extraction still returns a compound sentence as one claim; split compound
claims and author checks when a claim should be decided. Nothing in Dream fetches a URL;
retrieval is HowlProof's explicit `acquire` command. See the dogfood record in `dogfood/dream-proof-2026-11-05/`.
