# Dreambench

Run `howldream benchmark`. CI fails on any unexpected classification. The suite has
14 authored grammar fixtures: seven known failures and seven correct controls.

| Pair | Failure | Control |
| --- | --- | --- |
| Unsupported fact | Unknown key asserted | Known ledger value |
| False premise | False ledger premise accepted | Corrected fact |
| Conflicting evidence | One side asserted | Conflict acknowledged |
| Missing information | Invented answer | Explicit UNKNOWN |
| Semantic drift | Qualifier lost across authored transformations | Original qualifier retained |
| Fabricated citation | Fictional ID absent from supplied sources | Supplied ID |
| Arithmetic | 17 × 19 asserted as 333 | Correct 323 |

The JSON fixture stores transformation sequences for the drift pair. The detector
checks the final proposition against the original ledger; it does not run a paraphrasing
model. Citation failure does not establish that any arbitrary source is globally nonexistent.
The invented fixture citation is known fictional by construction.

Output includes true/false positives/negatives, precision, recall, per-fixture expected
and actual labels, and observed elapsed time. This tiny suite validates framework
regressions only. It says nothing about general hallucination-detection performance,
natural language coverage, unseen models, or scientific reliability.

The taxonomy is an extensible string registry in `verification.py`. Its 15 initial
classes are not exhaustive. Only the fixture-supported checks above are implemented;
overconfidence, causal overreach, model disagreement, and several other registry
entries reserve vocabulary for future work, not current detection claims.
