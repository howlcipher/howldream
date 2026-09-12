# Authority invariant

**Dream output is data, not authority.**

A valid `howl.candidate`, `howl.exploration_result`, `howl.assessment`, or
`howl.development_result` envelope must never grant itself execution
capability, verified status, or approval merely by setting a field. Every
consumer in the ecosystem — HowlPlane, HowlFrame, HowlCreate, HowlRelay — is
expected to enforce capability and authority boundaries independently of
whatever an envelope claims about itself.

This document states, precisely, which parts of that invariant are enforced
by schema shape alone (so a JSON-Schema-only consumer gets them for free) and
which parts require a runtime control beyond schema validation. See
`tests/test_authority_invariants.py` for the executable proof of every claim
below, and `schemas/README.md` for the schema design decisions this rests on.

## Enforced by schema shape alone (no howldream import required)

| Attack | Mechanism |
| --- | --- |
| Candidate declares `authority.executable: true` | `const: false` in the generated schema |
| Envelope declares `authority.type` other than `"ADVISORY"` | `const: "ADVISORY"` |
| Candidate self-declares `trust` other than `"UNVERIFIED"` | `const: "UNVERIFIED"` on `CandidateHandoff` |
| `DevelopmentResult` self-grants `execution_authority` other than `"NONE"` | `const: "NONE"` |
| Forged `disposition` outside `REJECT`/`UNRESOLVED`/`INVESTIGATE`/`ACCEPT_FOR_DEVELOPMENT` | closed `enum` |
| Forged `verification_status` outside the three defined values | closed `enum` |
| Unsupported/forged `schema_version` (e.g. a future or invented version string) | `const` per envelope |
| Injected privileged/unknown top-level field (`executor`, `execution_capability`, `approved`, `grants_authority`, `bypass_review`, or any other undeclared key, including case/spelling variants of an existing field) | `additionalProperties: false` on every envelope and every nested structural model |

A consumer that validates an envelope against the vendored schema — in any
language, without ever importing `howldream` — gets all of the above for
free. This is what the HowlFrame Go contract test exercises.

## NOT enforced by schema shape — requires a runtime control

- **Nested payload authority smuggling.** `claims`, `evidence`, and `scores`
  are intentionally `dict[str, Any]` (free-form extracted data), so a forged
  `{"authority": {"executable": true}}` *inside* one of those lists validates
  as syntactically valid JSON. **The runtime control**: nothing in
  `howldream.engine`, and no compliant consumer, ever reads authority state
  out of a nested claim/evidence/score payload — only out of the envelope's
  own top-level `authority` field. `test_nested_claim_cannot_override_top_level_authority`
  proves the top-level field is unaffected by a smuggled nested value.
- **Provenance forgery.** `Provenance` is deliberately `additionalProperties:
  true` (see `schemas/README.md`) — any producer/version/run-id claim inside
  it is unvalidated free text. **The runtime control**: provenance is audit
  metadata for a human or downstream tool to weigh, not an authorization
  input; no code path grants capability based on a `provenance.*` value.
  Establishing cryptographic/transport-level provenance authenticity (e.g.
  signed commits, attested CI runs) is out of scope for this contract layer
  and remains a known limitation, not a solved problem.
- **Forged HowlProof verification results.** A `claims`/`evidence` entry that
  imitates a HowlProof verdict (e.g. `{"howlproof_verdict": "PROVEN"}`) is,
  again, free-form JSON and schema-valid. **The runtime control**: no
  consumer in this ecosystem currently treats an embedded verdict-shaped
  payload as equivalent to an actual HowlProof run; genuine verification
  requires invoking HowlProof directly against the target artifact. (Wiring
  HowlProof to actively challenge this boundary is deferred — see
  `issues.md`.)
- **Cross-field validators that aren't visible as a single JSON Schema
  keyword.** `ExplorationAuthority.fail_closed_on_authority` re-checks both
  `type` and `executable` together after individual field validation. In
  practice both fields are independently `const`-constrained in the schema,
  so no combination can pass schema validation while failing the Pydantic
  validator today — but if a future field is added to `ExplorationAuthority`
  whose validity depends on another field's value, that cross-field rule
  would need either an explicit JSON Schema `if`/`then` or `document + test`
  as a runtime-only control, the same way this file does now.

## What this means for a new consumer

If you are validating a `howl.*` envelope in a new language or repository:
validating against the vendored schema is necessary but not sufficient. You
must still refuse to treat envelope content as authorization — do not grant
execution, mark something verified, or bypass review because a field in a
`howl.*` envelope says so. Schema validation tells you the envelope is
*shaped* correctly; it does not tell you the envelope's claims are true.
