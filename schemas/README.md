# `howl.*` ecosystem contract schemas

This directory contains **generated** JSON Schema (2020-12) for every versioned
`howl.*` envelope HowlDream produces or consumes. It exists so sibling
repositories can validate envelopes without importing the `howldream` Python
package or reimplementing its Pydantic models.

## Authoritative source

`src/howldream/contracts.py` is the single authoritative definition of every
`howl.*` contract. These `.schema.json` files are **generated from it** by
`scripts/generate_schemas.py` — never hand-authored, never hand-edited. If you
need to change a contract's shape, change `contracts.py` and regenerate:

```
python scripts/generate_schemas.py
```

CI runs `python scripts/generate_schemas.py --check` and fails the build if
`schemas/` has drifted from `contracts.py` (i.e. someone changed a model
without regenerating). This is the drift-detection mechanism referenced in
`howldream/issues.md`.

## Current contract families

| File | Envelope | Produced by | Consumed by |
| --- | --- | --- | --- |
| `howl.exploration.v1.schema.json` | `ExplorationRequest` (`howl.exploration/v1`) | HowlPlane (or any requester) | HowlDream |
| `howl.candidate.v1.schema.json` | `CandidateHandoff` (`howl.candidate/v1`) | HowlDream | HowlFrame, HowlCreate |
| `howl.assessment.v1.schema.json` | `CandidateAssessment` (`howl.assessment/v1`) | HowlFrame | HowlCreate, HowlDream |
| `howl.development_result.v1.schema.json` | `DevelopmentResult` (`howl.development_result/v1`) | HowlCreate | downstream review |
| `howl.exploration_result.v1.schema.json` | `ExplorationResult` (`howl.exploration_result/v1`) | HowlDream | HowlPlane, HowlRelay |

This list was derived by finding every model in `contracts.py` carrying a
`schema_version: Literal[...]` field. If a new envelope family is added to
`contracts.py`, add it to `ENVELOPES` in `scripts/generate_schemas.py` — the
drift check will not catch a family that was never added to the generator.

## Schema design decisions (intentional, not incidental)

- **`additionalProperties: false`** on every top-level envelope and on nested
  structural models (e.g. `ExplorationAuthority`) mirrors `extra="forbid"` on
  their Pydantic `StrictModel` base. An envelope cannot smuggle in an unknown
  field — including an unknown authority/capability field — and still
  validate.
- **`Provenance` is the one deliberate exception**: `additionalProperties:
  true`. Provenance is descriptive audit metadata, not an authority or
  structural boundary, and producers have historically attached ad hoc extra
  keys. The named `Provenance` fields (`run_id`, `producer_component`,
  `producer_version`, `model_or_provider`, `observation_kind`, `created_at`,
  `transformations`) are the canonical, cross-cutting concepts every producer
  should populate going forward; anything else is preserved but unvalidated.
- **Authority fields are `const`, not just typed.** `ExplorationAuthority.type`
  is `const: "ADVISORY"` and `.executable` is `const: false`. A schema
  validator alone is sufficient to reject a forged `"executable": true` or
  `"type": "EXECUTABLE"` — this is one authority boundary that schema
  validation *can* enforce by itself. Others (e.g. cross-field consistency)
  are enforced only by HowlDream's own Pydantic validators at construction
  time; see the "Authority invariant" section below for what that means for
  a schema-only consumer.
- **`trust: "UNVERIFIED"` and `execution_authority: "NONE"` are also `const`.**
  No `CandidateHandoff` can validate with any other `trust` value, and no
  `DevelopmentResult` can validate with any other `execution_authority` value.
  A candidate cannot self-declare verification or execution authority merely
  by setting a field — see `AUTHORITY_INVARIANT.md` (root of this repo) and
  `tests/test_authority_invariants.py` for the negative tests proving this.

## Versioning / evolution policy

- The `v1` in each filename and each `schema_version` literal is the contract
  version, not the package version. `contracts.py`'s Pydantic models and this
  directory move together.
- **Backward-compatible (stays within `v1`)**: adding a new *optional* field
  with a default, widening an enum, relaxing a length/pattern constraint,
  adding a new envelope family. Regenerate; the `v1` filename and
  `schema_version` const are unchanged.
- **Breaking (requires a new version)**: removing/renaming a required field,
  narrowing an enum, changing a field's type, tightening
  `additionalProperties`. This requires a new `schema_version` literal (e.g.
  `howl.candidate/v2`), a new model, and a new `howl.candidate.v2.schema.json`
  file. The `v1` file and model are retained for a compatibility window so
  existing consumers do not break on upgrade; do not delete a version file
  just because a newer one exists.
- `$id` for each schema points at its file's location on `main` — it is a
  stable identity URI, not a promise that this exact byte content never
  changes for compatible edits. Consumers that need a fixed byte-for-byte copy
  should vendor a specific commit (see below), not resolve `$id` live.

## Distribution model: vendored, pinned copies

We evaluated four distribution models for these contracts:

- **(A) Vendored copies pinned to a source commit** — chosen.
- (B) Schemas published as part of a versioned HowlDream package/release —
  not chosen; HowlDream doesn't currently cut package releases on a cadence
  that ecosystem consumers track, and this would add release-process
  machinery not otherwise needed yet.
- (C) A standalone `howl-contracts` package/repository — not chosen. All
  producing/consuming repositories are owned by the same org with full git
  access, and there is no evidence yet that contract ownership has actually
  diverged from HowlDream. Standing up a new repo now would be premature
  infrastructure for a problem that doesn't exist yet.
- (D) Repository-local reimplementations — not chosen; this is exactly the
  "hand-authored schemas that merely resemble the models" failure mode this
  work exists to close.

Each consumer vendors a copy of the schema file(s) it needs, plus a record of
the exact HowlDream commit SHA they were generated from (e.g. a `SOURCE.md`
or `VERSION` file alongside the vendored copy). Re-vendoring is a manual,
deliberate act — bumping the pin is a visible diff, not a silent drift.
Revisit this decision (toward B or C) if/when a second organization
independently owns or consumes these contracts.

## What is *not* proven by schema validation alone

Schema validation proves an envelope is *shaped* correctly. It does not, by
itself, prove:

- the envelope was actually produced by the component it claims (`provenance`
  is unvalidated free text for any consumer that only does JSON Schema
  validation — provenance forgery is a runtime/transport-layer concern, not a
  schema one);
- that a `CandidateAssessment`'s `disposition` reflects a real evaluation
  (a schema-only consumer cannot tell a genuine `ACCEPT_FOR_DEVELOPMENT` from
  a fabricated one — that requires verifying the producing component's
  identity/signature, which is out of scope for this contract layer);
- that a HowlProof verification result attached anywhere in a `claims` or
  `evidence` list is genuine (those fields are `dict[str, Any]` payloads by
  design, so a forged verification result inside them is syntactically valid
  JSON — the *runtime* control here is that no envelope field grants
  execution capability regardless of what its payload claims; see
  `AUTHORITY_INVARIANT.md`).

Consumers must keep enforcing capability/authority boundaries independently;
these schemas make the *shape* of the ecosystem boundary machine-checkable,
not the trustworthiness of what's inside it.
