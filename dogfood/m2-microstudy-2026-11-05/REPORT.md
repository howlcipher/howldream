# M2 Empirical Micro-Study Report: 3-Candidate Verification

**Date:** 2026-11-05  
**Component Baseline:** HowlProof `main` (`5bc25f0`), HowlDream `dogfood/m2-microstudy`  
**Execution:** Complete CLI round-trip:  
`howldream export-proof` → `howlproof acquire` → `howlproof evaluate --acquisition-store` → `howldream import-proof`

---

## 1. Objective

As recommended in M2 Deliverable J, this micro-study validates end-to-end operator workflow ergonomics and skeptical verification boundaries across three distinct candidate archetypes before initiating any large-scale research reruns.

The three candidates represent:
1. **Candidate 1 (`micro/01-mame-benchmark`)**: A real empirical benchmark measurement citing primary-source repository documentation with a verified methodology quote.
2. **Candidate 2 (`micro/02-cross-lang-cost`)**: A cross-language cost and token reduction comparison contrasting authentic measurement, deterministic calculation on unverified data, and unverified placeholder marketing claims.
3. **Candidate 3 (`micro/03-scoped-mutant`)**: Scoped documentation feature verification, verifying that a narrow refutation of one document does not falsely reject the overall candidate.

---

## 2. Candidate Results Summary

| Candidate ID | Claim ID | Category | Check Type | Evidence & Trust | Proof Result | Dream Disposition | Verification Impact |
|---|---|---|---|---|---|---|---|
| `micro/01-mame-benchmark` | `c01-ruby-generation-time` | EMPIRICAL | `fact_compare` (`ruby_time_seconds approx 73.1 s`) | Acquired from `mame/ai-coding-lang-bench`, methodology quote verified | `SUPPORTED` (VERIFIED) | `INVESTIGATE` (MEDIUM) | Real benchmark verified against primary source; development approval explicitly withheld (`NOT_GRANTED`). |
| `micro/02-cross-lang-cost` | `c02-ruby-cost` | EMPIRICAL | `fact_compare` (`ruby_cost approx $0.36`) | Acquired from `mame/ai-coding-lang-bench`, methodology quote verified | `SUPPORTED` (VERIFIED) | `UNRESOLVED` (LOW) | Source-verified measurement. |
| `micro/02-cross-lang-cost` | `c02-cost-reduction-arithmetic` | TECHNICAL | `arithmetic` (`(0.62-0.36)/0.62 = 0.419`) | Closed grammar calculation | `SUPPORTED` (VERIFIED) | (Contributes to above) | Calculation passes; `input_provenance` marked `UNVERIFIED`; origin `NOT_EXAMINED`. |
| `micro/02-cross-lang-cost` | `c02-placeholder-token-reduction` | EMPIRICAL | `fact_compare` (`token_reduction_pct approx 65%`) | `https://example.org/bench-token-study-a` (No acquisition) | `INCONCLUSIVE` (UNAVAILABLE) | (Forces `UNRESOLVED`) | Placeholder URL detected; math matches (`SUPPLIED_DATA_AGREES`), but empirical authority withheld. |
| `micro/03-scoped-mutant` | `c03-mutant-readme-agent` | EMPIRICAL | `text_presence` (`agent` in README) | Acquired `mutant_README.md` | `REFUTED` (FAILED, `scope_limited: true`) | `INVESTIGATE` (LOW) | Scope-limited refutation: Proof records `also_found_in: ["mutant_skill"]` and leaves broader question unevaluated. |
| `micro/03-scoped-mutant` | `c03-mutant-skill-agent` | EMPIRICAL | `text_presence` (`agent` in SKILL.md) | Acquired `mutant_SKILL.md` | `SUPPORTED` (VERIFIED, `scope_limited: true`) | (Contributes to above) | Confirms agent skill file exists in repo; Dream disposition remains `INVESTIGATE` (never `REJECT` or `ACCEPT_FOR_DEVELOPMENT`). |

---

## 3. Detailed Architectural Observations

### A. Candidate 1: Real Primary-Source Verification
- **Methodology Grounding**: Proof required and verified the verbatim methodology quote:
  `"We asked Claude Code (Opus 4.6) to implement a **mini-git** — a simplified version of Git"` (exceeding 25 chars and 4 words).
- **Structural Relevance**: All `subject_terms` (`Ruby`, `Claude Code`, `mini-git`) and the fact `73.1 s` were physically located in the acquired source text.
- **Authority Invariant**: Even though 100% of claims were `SUPPORTED` and integrity was verified, HowlDream's disposition was `INVESTIGATE` (never `ACCEPT_FOR_DEVELOPMENT`). The assessment summary row recorded:
  ```json
  "evidence_status": "ALL_CLAIMS_SOURCE_VERIFIED",
  "development_approval": "NOT_GRANTED"
  ```

### B. Candidate 2: Separation of Math vs Truth & Placeholder Suppression
- The arithmetic check `(0.62 - 0.36) / 0.62 = 0.419` was verified deterministically, reporting `evidence_status: DETERMINISTIC_CHECK_ONLY` with `input_provenance: UNVERIFIED`.
- The placeholder token reduction claim (`example.org`) correctly failed verification: despite the supplied numbers agreeing with the check, HowlProof returned `INCONCLUSIVE` with origin `PLACEHOLDER` and `evidence_status: SUPPLIED_DATA_AGREES`.
- In HowlDream, the presence of one unresolved claim kept the entire candidate at `UNRESOLVED` (LOW confidence), ensuring fabricated marketing metrics cannot slip through alongside legitimate arithmetic.

### C. Candidate 3: Scoped Semantic Invariants
- `mutant_README.md` lacked the term `agent`. Rather than an unadorned refutation that would condemn the candidate, HowlProof marked `scope_limited: true` and surfaced `also_found_in: ["mutant_skill"]`.
- `howldream import-proof` recognized the refutation as scope-limited, mapping the overall disposition to `INVESTIGATE` rather than `REJECT`.
- Neither candidate was promoted to development.

---

## 4. How to Reproduce

Run the micro-study script:
```bash
cd /run/media/howlcipher/tallgeese/dev/howldream
.venv/bin/python dogfood/m2-microstudy-2026-11-05/run_microstudy.py
```

All commands, exit codes, and outputs are captured under:
- `dogfood/m2-microstudy-2026-11-05/logs/commands.json`
- `dogfood/m2-microstudy-2026-11-05/results/summary.json`
