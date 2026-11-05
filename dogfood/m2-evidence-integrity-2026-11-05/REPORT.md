# M2 dogfood: evidence integrity on the Ruby Renaissance v4 corpus

Date 2026-11-05. HowlProof `feat/m2-evidence-integrity` @ `94c583f`; HowlDream
`feat/m2-evidence-integrity` (bridge commit `a160b57`). Both real CLIs were run:
`howldream export-proof` → `howlproof acquire` / `howlproof evaluate` → `howldream import-proof`.
Reproduce with `run_dogfood.py` (absolute paths inside; it rebuilds everything but never touches
the v4 archives). `commands.json` lists every command and exit code.

## What was and was not touched

* v4 archives are unmodified. Verified: no archive file is newer than the start of this work;
  Claude's `FROZEN.sha256` and `raw/web_SHA256SUMS` pass; the AGY bundle copies used here are
  byte-identical to the originals.
* Inputs: AGY's frozen bundles `cand-01-rubydex-mcp` and `cand-03-rubypack` (evaluated as authored,
  never edited), and Claude's seven preserved raw pages (`acquisition_store/raw/`).
* Honesty about the corpus: claims `k02-3`, `k02-5`, `k03-3`, `k06-3` carry Claude's v4 wording and
  checks verbatim (`k02-3` gained `subject_terms`). The v4 archives held no explicit outdated-fact
  claim and no deliberate irrelevant-document claim, so `ruby-4-0-0-latest` and
  `rubydex-index-time` were **constructed from archived facts**. `k02-3-scoped` and `rel-4-0-9` are
  new checks on the v4 wording. Wording was not tuned to get a particular outcome.
* Provenance of Claude-side sources: seven `OPERATOR_FILE` records, i.e. the files Claude downloaded
  in v4, attested (not observed) by the operator, with the source URLs recorded in
  `11_sources.md`. One extra `RETRIEVED` record: a live `howlproof acquire --url
  https://www.ruby-lang.org/en/news/` (HTTP 200, 2026-11-05T22:10:41Z). It had the same sha256
  (`80f142e9…`) as Claude's archived capture, so Proof reports the two as `DUPLICATES_ONLY`.
  That was the only network use: one bounded GET.

## AGY: placeholder and unsourced evidence (frozen bundles, no acquisition ever existed)

| Claim | Old Proof (50ded98) | M2 Proof | `check_outcome` | Origin | `evidence_status` |
|---|---|---|---|---|---|
| c01_01 Rubydex <50 ms (railsatscale.com URL, never fetched) | SUPPORTED / VERIFIED | INCONCLUSIVE | SUPPORTED | CLAIMED_ONLY | SUPPLIED_DATA_AGREES |
| c01_02 token reduction ≈65% (example.org) | SUPPORTED / VERIFIED | INCONCLUSIVE | SUPPORTED | PLACEHOLDER | SUPPLIED_DATA_AGREES |
| c01_03 "zero hallucination" (example.org) | REFUTED / FAILED | INCONCLUSIVE | REFUTED | PLACEHOLDER | SUPPLIED_DATA_CONTRADICTS |
| c01_04 adoption forecast | REQUIRES_EXTERNAL_VALIDATION | same | none | NOT_EXAMINED | UNRESOLVED |
| c03_01 RubyPack binary ≤35 MB (example.org) | SUPPORTED / VERIFIED | INCONCLUSIVE | SUPPORTED | PLACEHOLDER | SUPPLIED_DATA_AGREES |
| c03_02 startup ≈12 ms (conflicting, example.org) | INCONCLUSIVE | INCONCLUSIVE | none | PLACEHOLDER | UNRESOLVED |
| c03_03 100% C-extension compatibility (example.org) | REFUTED / FAILED | INCONCLUSIVE | REFUTED | PLACEHOLDER | SUPPLIED_DATA_CONTRADICTS |

Dream imports: both candidates `UNRESOLVED` (never `ACCEPT_FOR_DEVELOPMENT`). The v4 false
`SUPPORTED`/`VERIFIED` results (c01_01, c01_02, c03_01) no longer occur, and the *refutations* from
fabricated contradicting data are also withheld, since fabricated counter-evidence is no more
authoritative than fabricated support.

## Claude corpus (acquisition store supplied)

Proof overall verdict `INSUFFICIENT_EVIDENCE` (`no_acceptance_criteria`: no acceptance contract was
invented). Dream disposition `INVESTIGATE`: "2 claim(s) refuted (2 only within a limited scope); 4
unresolved". Summary row: `PARTIALLY_VERIFIED`, `development_approval: NOT_GRANTED`. Importing
twice gave an identical assessment.

| Claim (v4 wording) | Old Proof | M2, no store | M2, with store | `check_outcome` | `evidence_status` / notes |
|---|---|---|---|---|---|
| k02-3 The Mutant README documents an AI-agent integration (as authored: fact `agent_integration_documented: 0`) | REFUTED | INCONCLUSIVE | INCONCLUSIVE | REFUTED | SUPPLIED_DATA_CONTRADICTS: the agent-coded `0` is not in the README |
| k02-3-scoped (same wording, `text_presence "agent"`) | INCONCLUSIVE (unsupported check) | INCONCLUSIVE | **REFUTED, scope_limited** | REFUTED | SOURCE_VERIFIED_SCOPED; `also_found_in: [mutant_skill]`; `broader_question: NOT_EVALUATED` |
| k02-5 repo ships SKILL.md (as authored: HTTP status `200`) | SUPPORTED | INCONCLUSIVE | INCONCLUSIVE | SUPPORTED | `200` is HTTP metadata, not source text; unresolved |
| rel-4-0-9 Ruby 4.0.9 has been released (page text) | INCONCLUSIVE | INCONCLUSIVE | **SUPPORTED, scope_limited** | SUPPORTED | SOURCE_VERIFIED_SCOPED; origin OBSERVED_ACQUISITION; corroboration DUPLICATES_ONLY |
| k03-3 (0.62-0.36)/0.62 = 0.419 (as authored) | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | DETERMINISTIC_CHECK_ONLY; `input_provenance: UNVERIFIED`; origin NOT_EXAMINED |
| k06-3 Ruby returns to TIOBE top 10 by 2028 (as authored) | REQUIRES_EXTERNAL_VALIDATION | same | same | none | UNRESOLVED |
| ruby-4-0-0-latest (constructed) | INCONCLUSIVE | INCONCLUSIVE | **REFUTED, scope_limited** | REFUTED | SOURCE_VERIFIED_SCOPED, corroboration SEPARATE_ARTIFACTS_ORIGIN_UNASSESSED |
| rubydex-index-time (constructed; a genuine rv README that contains `1.8 seconds`) | **SUPPORTED** | INCONCLUSIVE | INCONCLUSIVE | SUPPORTED | relevance NOT_ESTABLISHED: subject term `Rubydex` is not in the page |

What the table shows:

* **Mutant.** The v4 failure (README lacks it, repo ships SKILL.md) is now reported as what it is:
  a refutation of one file's text, flagged `scope_limited`, with the related artifact surfaced and
  the broader question explicitly unevaluated. Dream maps it to `INVESTIGATE`, not `REJECT`.
* **Irrelevant but genuine document.** The old evaluator returned SUPPORTED because a number
  matched; M2 does not, because the page never mentions Rubydex.
* **Deterministic arithmetic** stays SUPPORTED but is labelled as a check on unverified inputs.
* **Forecast** stays REQUIRES_EXTERNAL_VALIDATION.
* **Placeholder/unacquired evidence** gets nothing without a store (the "no store" column).

## Defects found by this dogfood (all fixed, with regression tests)

1. A forecast and an arithmetic claim reported the *origin of the evidence they cited* (e.g.
   `OBSERVED_ACQUISITION`) although nothing was checked against it. Now `NOT_EXAMINED`.
2. `also_found_in` listed an unrelated benchmark page because it contained the word "agent". Now it
   lists only artifacts that contain every subject term.
3. Reading the raw data: bare flag values such as `0`/`9` "appear" in almost any page, so they can
   no longer be located (agent-coded flags are not source quotations).

## Unresolved limitations surfaced here (not fixed; documented)

* `ruby400_notes.html` carries `published_at` 2025-12-25 but was captured in October 2026: its
  news sidebar already lists 4.0.9. So it is not an "older snapshot", and Proof (correctly) found
  no disagreement between it and the news page. `published_at` is an author-declared article date,
  not a capture time, and page chrome can postdate it. A genuinely old snapshot would be needed to
  show an outdated-versus-current conflict.
* `rel-4-0-9` establishes that the *page says* 4.0.9 was released; not that it was. The two
  acquisitions are the same bytes.
* The `OPERATOR_FILE` sources are attested by the operator (here, the same agent that authored the
  claims). That is a weaker origin than an independent retrieval and is labelled so.
* `claim_relevance` is structural only; `real_world_truth` is `UNRESOLVED` for every sourced claim;
  `corroborated` is `false` everywhere.
* This is an internally consistent, partly constructed corpus. It does not count as real-world proof
  of any Ruby ecosystem claim.
