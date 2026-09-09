# Independent review and remediation

Independent reviewer: core_review, correctness/security/test-falsifier roles.
Review used executable reproductions. All findings were accepted.

| Finding | Severity | Resolution |
| --- | --- | --- |
| Quoted JSON and structured secrets escaped redaction | High | Sensitive-key and quoted-key handling; regression |
| Decimal rounding falsely supported incorrect multiplication | Medium | Exact Fraction arithmetic; counterexample regression |
| Incomplete hash inventory allowed symlinks and altered authority | High | Exact inventory, symlink rejection, trust validation |
| Incomplete HTTP reads lost observations | Medium | HTTP protocol error normalization; partial evidence test |
| Saved remote replay configuration authorized credential egress | High | Fresh explicit --allow-remote required |
| Baseline-only redaction retained replay eligibility | Medium | Check both generated groups |
| WAKE retained only old implementation provenance | Medium | Separate current analysis provenance |
| Boolean/float schema version accepted as integer 1 | Low | Exact integer input validation |

Hashes remain integrity checks, not authentication. Review an imported endpoint
before explicitly authorizing remote replay. Local review also added unresolved
claim visibility and corrected invalid Git revision capture.

Final independent pass verified all fixes with 42 passing tests and found no
remaining blocking issue. It checked website and ecosystem content against the
observations. Rendered and live deployment checks are recorded separately.
