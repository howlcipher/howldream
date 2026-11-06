# Imagination & Anti-Reinvention Dogfood Study Report

**Date:** 2026-11-06  
**Pipeline:** HowlDream `main` $\longleftrightarrow$ HowlProof `main`  
**Protocol:** End-to-End CLI Dogfooding via `scripts/search_prior_art.py`, `howldream explore`, `howldream export-proof`, `howlproof evaluate`, and `howldream import-proof`.

---

## 1. Study Objective

This empirical dogfood study validates the complete lifecycle of AI imagination, anti-reinvention verification, and adversarial proof evaluation:
1. **Prior Art Gating**: Dreamed concepts are checked against existing published tools and standard architectural patterns using `scripts/search_prior_art.py`.
2. **Reinvention Rejection & Retrying**: Known tools (such as Redis-style key-value caches) are identified as `WHEEL_REINVENTED`, triggering the re-dreaming loop.
3. **Automated Check Derivation**: Novel candidates with quantitative propositions (`CALC:`) automatically derive strict mathematical checks without manual intervention.
4. **Adversarial Proof Evaluation**: HowlProof evaluates quantitative propositions under its `--profile research` harness, upholding `SUPPORTED` verdicts for correct math while refuting flawed claims.
5. **Round-Trip Governance**: `howldream import-proof` safely integrates the proof results into candidate assessments, preserving authority boundaries (`development_approval: NOT_GRANTED`).

---

## 2. Empirical Verification Results

| Candidate ID | Nature | Prior Art Filter | Derived Check | HowlProof Verdict | HowlDream Disposition | Authority & Integrity Outcome |
|---|---|---|---|---|---|---|
| `imagination/01-reinvented-cache` | Reinvented Concept | **CAPTURED** (Redis In-Memory Data Store) | N/A | N/A (Blocked by Prior Art) | `REJECTED` (`WHEEL_REINVENTED`) | Intercepted before promotion; triggers bounded retry loop with avoidance prompt. |
| `imagination/02-ring-dispatch-bus` | Novel Concept | **UNCAPTURED** (Clean) | `arithmetic: 65536 * 16 == 1048576` | `SUPPORTED` (`DETERMINISTIC_CHECK_ONLY`) | `INVESTIGATE` | Mathematical integrity verified; `development_approval: NOT_GRANTED`. |
| `imagination/03-flawed-math-allocator` | Negative Control | **UNCAPTURED** (Clean) | `arithmetic: 1024 / 4 == 512` | `REFUTED` (`CHECK_FAILED`) | `INVESTIGATE` (with Contradiction) | Calculation falsified (`256 != 512`); contradiction logged in finding ledger. |

---

## 3. Step-by-Step CLI Execution Record

### Phase 1: Prior Art Interception
The CLI search helper `scripts/search_prior_art.py` was executed directly against Candidate 1:
```json
{
  "captured": true,
  "matched": true,
  "title": "Redis In-Memory Data Store",
  "source_ref": "https://redis.io",
  "summary": "In-memory database and cache with optional disk persistence and pub/sub.",
  "matched_terms": [
    "redis",
    "in-memory key-value",
    "in-memory cache"
  ],
  "confidence": "HIGH"
}
```
When integrated with `howldream explore --prior-art-command "python scripts/search_prior_art.py {query}"`, the candidate is marked `WHEEL_REINVENTED` and the concept family (`PRIOR_ART:Redis In-Memory Data Store`) is fed into `explored_families`.

### Phase 2: Automated Check Derivation in `export-proof`
Candidate 2 declared a quantitative calculation `CALC: 65536 * 16 = 1048576`.
`howldream export-proof` automatically derived the verification check:
```json
{
  "expected": "1048576",
  "expression": "65536 * 16",
  "op": "eq",
  "type": "arithmetic"
}
```

### Phase 3: Adversarial Proof Evaluation
HowlProof evaluated both Candidate 2 and Candidate 3 under `--profile research`:
- **Candidate 2 (Valid math)**:
  - Evaluation result: `SUPPORTED`
  - Evidence status: `DETERMINISTIC_CHECK_ONLY`
- **Candidate 3 (Flawed math)**:
  - Evaluation result: `REFUTED`
  - Evidence status: `DETERMINISTIC_CHECK_ONLY`

### Phase 4: Round-Trip Assessment Import
`howldream import-proof` imported both assessment records:
- Candidate 2 disposition: `INVESTIGATE` (Contradictions: 0)
- Candidate 3 disposition: `REJECT` (Contradictions: 1)

---

## 4. How to Reproduce

Run the study directly from the HowlDream repository root:
```bash
python dogfood/imagination-2026-11-06/run_study.py
```
All intermediate bundles, logs, and assessments are written into subdirectories under `dogfood/imagination-2026-11-06/`.
