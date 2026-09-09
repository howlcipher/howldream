# Milestone verification evidence

Final local Python suite: 43 passed, zero failures, zero skips (Python 3.14.4).
Ruff formatting/check, flake8 with README flags, and mypy pass. Wheel and source
distribution build. Dreambench: 14 fixtures, 7 TP, 7 TN, 0 FP, 0 FN, precision/recall
1.0 on these authored fixtures only. Artifact: dogfood/benchmark.json.

CLI exercised: help, version, validate, run, nightmare, wake, replay, inspect,
compare and report. Contract tests also cover generation-only DREAM and
end-to-end generation/verification. The final mock run and replay in dogfood/final
and dogfood/final_replay have identical candidate texts and metrics. NIGHTMARE
and its WAKE descendant are retained separately. Original local model output and
later re-analysis remain under dogfood/local and dogfood/wake.

Pages rendered at 375, 768 and 1440 pixels: title, description, landmarks,
keyboard skip link, fragment navigation and no document overflow pass. Desktop
and mobile screenshots inspected. The canonical hub's existing suite passes
30/30 responsive/interaction checks across nine viewport sizes; its SEO checks,
Go tests and Go vet pass. The new Ecosystem page has a dedicated CI browser check.

Dependency audit passes after updating the virtual environment's pip. Initial
GitHub Python 3.11 CI found a vulnerable preinstalled setuptools; CI now upgrades
both pip and setuptools before auditing. Audit thresholds were not lowered.
Bandit reports zero medium/high findings and four low findings for fixed
subprocess/HTTP primitives. These use fixed Git arguments, validated HTTP(S)
endpoints, disabled redirects/proxies, and bounded timeouts. No generated command
or arbitrary URL verifier is executed.

Secret scan findings were inspected: SHA-256 provenance values and fake negative
test credentials. No actual credentials identified. This is not a guarantee
that redaction detects every possible sensitive string.

Commits are SSH-signed with the existing local signing key. GitHub reports
unknown_key for that key rather than Verified; no account key registrations or
security settings were changed. See GitHub Actions and merged PRs for live CI
and deployment status; these may run after the evidence document is committed.
