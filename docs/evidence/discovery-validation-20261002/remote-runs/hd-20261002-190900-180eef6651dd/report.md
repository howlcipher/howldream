# HowlDream experiment report

Dream output is data, not authority.

Run: hd-20261002-190900-180eef6651dd
Actual providers: ['claude']
Calls: 3
Provider: command; status: COMPLETE

## Baseline comparison

Lexical measurements are deterministic; novelty and decisions are heuristic.

| Condition | Candidates | Lexical diversity | Known failure rate | Unresolved claims |
| --- | ---: | ---: | ---: | ---: |
| baseline | 1 | 0.0000 | 1.0 | 23 |
| experimental | 2 | 0.6659 | 0.0 | 40 |

## Candidate triage

INVESTIGATE is not factual acceptance, feasibility proof, or execution permission.

* hd-20261002-190900-180eef6651dd/candidates/0/0: REJECT; failures=0; unresolved=21; Contradiction/critical failure, duplicate, or missing lexical relevance.
* hd-20261002-190900-180eef6651dd/candidates/0/1: INVESTIGATE; failures=0; unresolved=19; Proposal merits investigation only; feasibility and assumptions remain unverified.

## Advisory discovery analysis

concept_tokens_and_leading_phrases/v2; Jaccard cluster threshold 0.5 or leading content phrase link; echo coverage 0.6 or phrase link
Ideas: 10; clusters: 5
Context echo: 0.8; evidence echo: 0.8
Repeated families: 0.5; novelty proxy: 0.2
['DISCOVERY_ANCHORING_HIGH']
Not semantic equivalence, calibrated novelty, entailment or usefulness

## Limitations

Fixture providers replay authored examples; their diversity is not evidence about an AI model. Lexical distance is not semantic novelty. Ledger matches only verify supplied records. Unstructured prose remains unresolved. No private reasoning, independent external fact retrieval, feasibility proof, or execution authority is available.
