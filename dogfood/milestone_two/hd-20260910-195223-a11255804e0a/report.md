# HowlDream experiment report

Dream output is data, not authority.

Run: hd-20260910-195223-a11255804e0a
Provider: ollama; status: COMPLETE

## Baseline comparison

Lexical measurements are deterministic; novelty and decisions are heuristic.

| Condition | Candidates | Lexical diversity | Known failure rate | Unresolved claims |
| --- | ---: | ---: | ---: | ---: |
| baseline | 3 | 0.4721 | 1.0 | 16 |
| experimental | 5 | 0.7772 | 0.4 | 40 |

## Candidate triage

INVESTIGATE is not factual acceptance, feasibility proof, or execution permission.

* hd-20260910-195223-a11255804e0a/candidates/0/0: INVESTIGATE; failures=0; unresolved=4; Proposal merits investigation only; feasibility and assumptions remain unverified.
* hd-20260910-195223-a11255804e0a/candidates/0/1: REJECT; failures=1; unresolved=8; Failure, duplicate, or missing lexical relevance.
* hd-20260910-195223-a11255804e0a/candidates/0/2: INVESTIGATE; failures=0; unresolved=2; Proposal merits investigation only; feasibility and assumptions remain unverified.
* hd-20260910-195223-a11255804e0a/candidates/0/3: INVESTIGATE; failures=0; unresolved=9; Proposal merits investigation only; feasibility and assumptions remain unverified.
* hd-20260910-195223-a11255804e0a/candidates/0/4: REJECT; failures=1; unresolved=17; Failure, duplicate, or missing lexical relevance.

## Limitations

Fixture providers replay authored examples; their diversity is not evidence about an AI model. Lexical distance is not semantic novelty. Ledger matches only verify supplied records. Unstructured prose remains unresolved. No private reasoning, independent external fact retrieval, feasibility proof, or execution authority is available.
