# HowlProof result

HowlProof judges. It does not repair the artifact it is judging.

Artifact: bundle
Commit: 1abdbff9e0c2811aea32135a84ec4275be4fe87d
Branch: feat/dream-proof-bridge (working tree dirty)
Run: hp-20261105-205948-851e9661fe36
Profiles: research
Completed: 2026-11-05T20:59:48.795196+00:00

## Verdict: INSUFFICIENT_EVIDENCE

The artifact may or may not be acceptable. The evaluation that ran was inadequate to make a defensible determination, so no determination is claimed.

Deciding rule: `no_acceptance_criteria`

- The artifact defines no acceptance criteria.
- Running checks without criteria shows activity, not conformance.

## Acceptance criteria

0 of 0 satisfied.

| Criterion | Requirement | Outcome | Detail |
| --- | --- | --- | --- |

## Checks

4 verified, 1 failed, 1 skipped, 4 unavailable, 0 not applicable, 0 errored.

| Check | Checker | Status | Mode | Note |
| --- | --- | --- | --- | --- |
| research.claims.bundle | research.claims/v1 | VERIFIED | REAL | claim bundle is well formed and 5 evidence file(s) match their registered digests |
| research.claims.c001 | research.claims/v1 | VERIFIED | REAL | claim rr-1-accurate: SUPPORTED |
| research.claims.c002 | research.claims/v1 | FAILED | REAL | claim rr-2-inaccurate: REFUTED |
| research.claims.c003 | research.claims/v1 | UNAVAILABLE | REAL | no grounded check was supplied for this claim; a citation or quotation is not proof, and any verification plan stays proposed until the author grounds it |
| research.claims.c004 | research.claims/v1 | VERIFIED | REAL | claim rr-4-currency: SUPPORTED |
| research.claims.c005 | research.claims/v1 | SKIPPED | REAL | value judgments and forecasts cannot be established by an automated check, and citations do not change that |
| research.claims.c006 | research.claims/v1 | VERIFIED | REAL | claim rr-6a-arithmetic: SUPPORTED |
| research.claims.c007 | research.claims/v1 | UNAVAILABLE | REAL | matching evidence exists but none is declared independent; evidence that is not independent cannot support or refute a claim |
| research.claims.c008 | research.claims/v1 | UNAVAILABLE | REAL | independent evidence conflicts (S5-tiobe-jul supports, S5-tiobe-sep contradicts); a newer source is not a resolution |
| research.claims.c009 | research.claims/v1 | UNAVAILABLE | REAL | no cited evidence is both usable and relevant to the compared fact (S1-ruby-4.0-notes: irrelevant) |

## Validation modes

- **REAL**: research.claims.bundle, research.claims.c001, research.claims.c002, research.claims.c004, research.claims.c006
- **SIMULATED**: none
- **SKIPPED**: research.claims.c005
- **UNAVAILABLE**: research.claims.c003, research.claims.c007, research.claims.c008, research.claims.c009
- **NOT_APPLICABLE**: none
- **ERROR**: none

## Findings

### HP-FUNC-0001 — Claim rr-2-inaccurate refuted by independent evidence

- Adversary: FUNCTIONAL
- Category: correctness
- Severity: HIGH
- Confidence: HIGH
- State: FOUND
- Blocking: no
- Location: not localised

claim rr-2-inaccurate: independent evidence S2-mini-git contradicts python_seconds approx 40 s

Evidence:

```
[
  {
    "id": "S2-mini-git",
    "independent": true,
    "integrity": "ok",
    "observed": "74.6 s",
    "published_at": "2026-03-01",
    "relation": "contradicts",
    "sha256": "8240d0eb65b45d53f39943f99a76b2a6fb2aa98c3a9fe669a999e85888901c5e",
    "source_type": "DERIVED_FROM_EXTERNAL_DATA"
  }
]
```

Recommended remediation (for the artifact's owner, not for HowlProof): Revise or withdraw the claim, or supply independent evidence that resolves the contradiction.


## Unresolved risks

- HP-FUNC-0001 (HIGH): claim rr-2-inaccurate: independent evidence S2-mini-git contradicts python_seconds approx 40 s

## Limitations

- research.claims.c003 was UNAVAILABLE: no grounded check was supplied for this claim; a citation or quotation is not proof, and any verification plan stays proposed until the author grounds it
- research.claims.c005 was SKIPPED: value judgments and forecasts cannot be established by an automated check, and citations do not change that
- research.claims.c007 was UNAVAILABLE: matching evidence exists but none is declared independent; evidence that is not independent cannot support or refute a claim
- research.claims.c008 was UNAVAILABLE: independent evidence conflicts (S5-tiobe-jul supports, S5-tiobe-sep contradicts); a newer source is not a resolution
- research.claims.c009 was UNAVAILABLE: no cited evidence is both usable and relevant to the compared fact (S1-ruby-4.0-notes: irrelevant)

## Notes

- no service is declared, so live adversaries have nothing to attack

--------------------------------------------------------------------

This report is advisory evidence. HowlProof does not promote, merge, deploy or approve anything. Remediation belongs to the artifact's builder and promotion to HowlPlane and HowlChangeOps.
