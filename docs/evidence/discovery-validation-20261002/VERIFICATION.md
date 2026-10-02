# Verification

| Repository | Integrated baseline | Final full local suite | Result |
| --- | ---: | ---: | --- |
| howldream | 204 | 235 | PASS |
| howlcreate | 78 | 90 | PASS |
| howl-provider-core | 37 | 37 | PASS; unchanged |
| Total | 319 | 362 | PASS |

All invocations set HOWL_FORBID_LOCAL_INFERENCE=1. Initial shared-venv collection lacked
provider-core imports; corrected with explicit sibling PYTHONPATH before baseline.
Complete suites include real Dream/Create imports and preserve legacy authority,
transport metadata, local-denial, hard-constraint, semantic completion, false-premise,
compact provenance, chronology, repair and checkpoint/resume cases.

Dream CI-equivalent checks: ruff format --check src tests scripts; ruff check src tests
scripts; flake8 src tests --max-line-length=100 --extend-ignore=E203,W503; mypy;
python scripts/generate_schemas.py --check; full pytest; python -m build; bandit -r src -ll;
benchmark dreambench development; DreamValue fixture evaluation; example validate/run;
Playwright site checks at 375/768/1440px; git diff --check. Dream ecosystem CI is pinned
to merged Create f198015977ef54c1f012ee2ebcff873cde1e39b1.

Create: full pytest; compileall src tests; flake8 src tests --select=F821,F401,E9;
scripts/test_seo.py; installed CLI and direct --from-dream scaffold; git diff --check.
Create PR #8 CI (Python 3.11/3.12/3.13) passed before merge.

Fresh mission verification environment installs both editable packages and the actual
pinned provider-core dependency. The pinned provider tree is identical to inspected
main d0054c4 (git diff empty). Tests also run in this clean environment; exact output
logs retained. A no-isolation build initially failed because the reused environment
lacked setuptools; the actual isolated CI build passes. A shared-environment audit found
urllib3 2.7.0 advisories. Fresh dependency resolution selects urllib3 2.8.0 and reports
no known vulnerabilities. Dedicated audit cache removes old-cache deserialization
warnings. Editable first-party packages/private distribution names are not audited by
PyPI advisory checks; their source receives tests and Bandit. No unrelated repo dependency
or provider rewrite was made. A direct -m Create CLI emitted a pre-existing runpy warning;
the installed entrypoint is the verified, warning-free workflow.

Test Impact Assessment: TIA.json plus local evidence-ledger.jsonl; `tia record` and
`tia check DISCOVERY-VALIDATION-20261002` pass using the live HowlPlane package entrypoint.
The ship-check prompt says `python -m src.control_plane`, but live source exposes
`python -m howlplane.control_plane`; use live evidence. This is a library-sync candidate,
not a reason to silently skip the gate. The authority boundary CLI passes for commit,
push and PR merge. User explicitly authorized the bounded remote smoke and final merge.
No production deployment, credentials change, external message, or product build occurred.

New tests cover all A-J mission patterns, including fake subjects, family paraphrases,
ledger withholding, typed operator expectations, citation-only diagnostics, continuation
prompts, direct Dream identity, low budgets, report-language mismatches, negative cluster
controls, and CONFLICT tradeoff handling. Fixtures do not establish model creativity.

The final broad source/test/config gate is rerun after code and CI edits. Published
Markdown evidence additions do not alter executable/test/config state. GitHub PR checks
must pass at the exact head before merge; no admin bypass or force update is used.
