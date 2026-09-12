# Backlog

Known gaps and follow-up work, ranked highest-value first. Opened 2026-09-11 during
a full audit of the Milestone Four "controlled native ecosystem integration" claims
(0.4.0), which turned out to be significantly overstated relative to what actually
exists and is CI-exercised in the sibling repos. See `change_log.md` (0.4.1) for the
correction this backlog follows from. When picking up an item, re-verify its status
against the live repos before starting — this audit is a point-in-time snapshot.

## Ranked backlog

| # | Item | Status | Owner repo(s) |
| --- | --- | --- | --- |
| 1 | [Publish JSON Schema for the `howl.*` contracts](#1-publish-json-schema-for-the-howl-contracts) | In progress | howldream (+ vendor into howlframe; howlplane, howlcreate, howlrelay next) |
| 2 | [Close the HowlPlane-side CI-exercise gap for `howldream`](#2-close-the-howlplane-side-ci-exercise-gap-for-howldream) | In progress | howlplane |
| 3 | [Merge the HowlFrame candidate_evaluator branch](#3-merge-the-howlframe-candidate_evaluator-branch) | Open | howlframe |
| 4 | [Replace the one-off dogfood run with a repeatable, path-agnostic reproduction](#4-replace-the-one-off-dogfood-run-with-a-repeatable-path-agnostic-reproduction) | Open | howldream |

## Details

### 1. Publish JSON Schema for the `howl.*` contracts

**Symptom:** `howl.exploration/v1`, `howl.candidate/v1`, `howl.assessment/v1`,
`howl.exploration_result/v1`, and `howl.development_result/v1` are defined only as
Pydantic models in `src/howldream/contracts.py`. There is no `.schema.json` (or
OpenAPI/protobuf) artifact anywhere in this repo or the sibling repos. Consumers
(HowlPlane, HowlCreate) get this contract only by directly importing the Python
package — confirmed by checking `howlplane/schemas/` (14 files, none matching) and
finding no equivalent schema files in howlcreate or howlrelay.

**Why it matters:** this is the structural root cause of items 2 above (the CI gaps)
— a consumer can't validate a `howl.candidate/v1` envelope without either importing
`howldream` directly (which is what's missing/untested today) or trusting an informal
dict-shape match (which is what HowlPlane's `DeterministicTestExplorationProvider`
and HowlRelay's file-reading adapter currently do). Compare to how HowlProof vendors
HowlPlane's JSON Schemas (`howlplane/schemas/*.schema.json`) and tests against them —
that pattern lets a consumer validate the contract without a Python dependency at all.

**Fix:** generate `.schema.json` files from the existing Pydantic models via
`model_json_schema()` (add a small `scripts/generate_schemas.py` and a CI check that
fails if the checked-in schemas drift from the models), publish them under e.g.
`schemas/` in this repo, and vendor copies into howlplane/howlcreate/howlrelay the way
HowlProof's schemas are vendored. This does not require any of the three consumers to
add a Python dependency on `howldream`.

**Acceptance:** a schema file exists per contract, is regenerated (not hand-edited),
and at least one sibling repo validates an envelope against the vendored copy in its
own test suite without importing `howldream`.

**Progress (2026-09-12):** `scripts/generate_schemas.py` now generates all five
`schemas/howl.*.v1.schema.json` files from `src/howldream/contracts.py`
(`model_json_schema()`), with `--check` drift detection wired into `.github/workflows/ci.yml`.
`schemas/README.md` documents the authoritative source, the vendoring architecture
decision (vendored copies pinned to a commit — see that file for the full comparison),
and the versioning/evolution policy. The previously-untyped `provenance: dict[str, Any]`
field on all five envelopes was replaced with a typed (but deliberately
`additionalProperties: true`) `Provenance` model — see `AUTHORITY_INVARIANT.md` for why
that field alone stays open while the rest of each envelope stays closed. New
`tests/test_authority_invariants.py` proves the authority/trust/execution-authority/
disposition/verification-status/schema-version invariants at both the Pydantic layer
and the generated-schema layer (100 tests). Still open: the HowlFrame Go consumer test
(in progress, tracked as part of this item since it's the acceptance bar) and vendoring
into howlplane/howlcreate/howlrelay. Not closing this item until a sibling repo's own
test suite actually validates against the vendored schema.

### 2. Close the HowlPlane-side CI-exercise gap for `howldream`

**Symptom:** `howlplane/src/control_plane/howldream_runner.py`'s
`NativeHowlDreamProvider.explore()` does a real `from howldream.contracts import
ExplorationRequest` / `from howldream.engine import explore`, but `howldream` is not
a declared dependency in HowlPlane's `pyproject.toml` and is not installed in
HowlPlane's CI (`test.yml` only runs `pip install .[all,dev]`). HowlPlane's own tests
(`tests/test_howldream_integration.py`) inject a `DeterministicTestExplorationProvider`
fake instead. This is the same class of gap as the HowlCreate↔HowlDream one this repo
just closed (see the 0.4.1 change log entry and the `ecosystem-integration` CI job),
but on the other repo and still open.

**Fix (owned by howlplane, mirror what this repo just did in `ecosystem-integration`
in `.github/workflows/ci.yml`):** add a CI job to howlplane that installs a pinned
`howldream` commit (`pip install "git+https://github.com/howlcipher/howldream.git@<ref>"`)
and asserts `NativeHowlDreamProvider.explore()` succeeds against the real package
before running its integration test suite.

**Acceptance:** HowlPlane's CI fails if the real `howldream` import breaks, not just
if the fake provider's contract shape changes.

### 3. Merge the HowlFrame candidate_evaluator branch

**Symptom:** `apps/candidate_evaluator/candidate_evaluator.howl` and its compiled
`.hfbc` exist only on an unmerged howlframe branch
(`feat/milestone-four-candidate-evaluator`), not on `main`. Every "HowlFrame
integration" claim in this repo's docs currently describes an artifact that doesn't
ship. Until this merges, `docs/architecture.md`/`docs/ecosystem.md`/`README.md`
should keep describing the in-process Python fallback as what actually runs (updated
in the 0.4.1 correction).

**Fix:** owned by howlframe — merge (or explicitly abandon and document why) the
`feat/milestone-four-candidate-evaluator` branch. Not something this repo can fix
directly; tracked here so the correction in 0.4.1 doesn't get silently stale again
once it does merge (the docs should flip back to describing it as real at that point).

**Acceptance:** `candidate_evaluator.hfbc` is reachable from a fresh `howlframe`
clone's `main` branch; this repo's docs are updated to reflect it.

### 4. Replace the one-off dogfood run with a repeatable, path-agnostic reproduction

**Symptom:** `dogfood/milestone_four/SUMMARY.md` and its backing run
(`hd-20260911-145551-873eea4f7922/`) were produced by `scripts/run_milestone_four_dogfood.py`
run once, manually, on this workstation. The 0.4.1 correction removed the
hardcoded sibling-checkout paths (`worktrees/howlframe-milestone-four`, etc.) in
favor of a `HOWLFRAME_HFBC_PATH` environment variable, so the script no longer
assumes a specific machine's directory layout — but it is still a manual script, not
a CI-gated or scheduled reproduction, and item 3 (HowlFrame not merged) means the
real bytecode path can't be exercised by anyone without a local howlframe build
today anyway.

**Fix:** once item 3 (HowlFrame merge) lands, re-run the dogfood script with
`HOWLFRAME_HFBC_PATH` pointed at a freshly built evaluator on a clean clone (not this
workstation) to confirm the fixed script is actually portable, and consider adding it
as a scheduled (not per-push) CI job so the evidence in `dogfood/milestone_four/`
stays reproducible rather than becoming another point-in-time claim.

**Acceptance:** the dogfood script runs successfully on a machine that is not this
one, producing an equivalent `SUMMARY.md`.
