# HowlDream Milestone Two evaluation report

## Abstract

Milestone Two evaluates whether HowlDream's narrow failure checks transfer beyond
the original 14 grammar fixtures and whether a transparent framework can measure
useful divergent generation. DreamBench 0.2.0 contains 156 authored,
template-derived cases and 312 claim annotations. DreamValue 0.1.0 contains 24
technical tasks and equal 240-candidate baseline and DREAM calibration pools.
The evidence does not justify ecosystem promotion.

## Research questions

DreamBench asks whether the extractor and deterministic verifiers detect
unsupported, contradictory, distorted, misattributed, and numerically wrong claims
without flagging grounded controls. DreamValue asks whether candidate sets can be
compared on conceptual uniqueness, duplication, unsupported assumptions,
investigation value, verification survival, cost, and diminishing returns.

## Methodology

DreamBench cases include provenance, severity, difficulty, split, evidence,
expected case classification, and claim-level labels. The 156 cases are split into
65 development, 26 validation, 39 held-out, and 26 confirmation cases. Sentence
boundaries are matched to annotations with token-set similarity at 0.45. Matched
claims are checked only against the supplied ledger, source-ID presence, or exact
arithmetic.

An early dry run exposed that hard extraction cases did not affect failure recall.
The pre-publication matrix was corrected. Because that inspection touched held-out
design, a confirmation partition was created and run once after detector logic
was frozen. This history is disclosed rather than treating the original held-out
partition as untouched.

DreamValue uses authored approach labels and review outcomes. Conceptual clusters
are exact human-authored approach identifiers. Verified Novel Candidate Yield is
the fraction of all candidates that belongs to a unique cluster, is relevant, has
no labeled unsupported or contradicted assumption, and is labeled INVESTIGATE or
SURVIVES_VERIFICATION. The blinded packet hides condition labels and supports
independent raters.

Deterministic approach labels are reproducible, offline, and inspectable.
Embeddings could recognize more paraphrases, but would add model-version dependence
and opaque thresholds. A future study may add them as a separately labeled heuristic.

## DreamBench results

The primary held-out split produced 0 TP, 0 FP, 65 TN, and 13 FN across 78 claims:
precision was undefined because nothing was flagged, recall was 0, and F1 was
undefined. Claim extraction coverage was 52 of 78 claims, or 0.6667, with 26
misses and 13 spurious sentence extractions. Every problematic hard-form claim was
missed upstream. Category recall was therefore 0.

The untouched confirmation split produced 13 TP, 0 FP, 39 TN, and 0 FN across 52
claims, with precision, recall, and F1 of 1.0. Category-label recall was only
0.3846 because broad failures do not reliably identify authored subtypes. The
sharp partition difference shows sensitivity to phrasing and template difficulty.

Across all partitions, the result was 52 TP, 0 FP, 234 TN, and 26 FN. Precision
was 1.0, recall 0.6667, and F1 0.8. These numbers describe this authored matrix
only. Exact category recall across all partitions was 0.2564. The narrow controls
cannot establish a real-world false-positive rate.

## Claim extraction results

Across 312 claim annotations, 273 relevant claims were matched, 39 were missed,
and 26 sentence extractions were spurious. Approximate coverage was 0.875 and
approximate precision was 0.9130. These are lexical operational estimates, not
semantic extraction scores.

## DreamValue results

The calibration pools use equal budgets: 240 baseline and 240 DREAM candidates.
Baseline lexical diversity was 0.6416, with 120 conceptual clusters, a 0.5
duplicate rate, no labeled unsupported candidates, and a 0.1 Verified Novel
Candidate Yield. DREAM lexical diversity was 0.6862, with 216 clusters, a 0.1
duplicate rate, a 0.3 unsupported rate, a 0.7 INVESTIGATE rate, a 0.3
verification-survival rate, and a 0.5 yield.

These results validate metric calculations against authored labels. They do not
show that live DREAM generation outperforms repeated baseline sampling. Independent
blinded human review is required before the comparison can support a causal claim.

## Divergence and candidate-count curves

The authored curve shows useful labels through divergence 0.8, then unsupported
and rejected candidates at 1.2 and 1.4. At three and five candidates per task the
pool contains only distinct accepted approaches. At ten, conceptual diversity
falls to 0.9, duplicate rate reaches 0.1, unsupported rate reaches 0.3, and yield
falls to 0.5. This is a designed calibration curve, not a provider sweet spot.

## Human review

The generated packet randomizes candidates with a fixed seed, omits condition
labels, and collects useful, novel, feasible, and worth-investigating judgments.
No agreement is reported because independent ratings have not been collected.

## Dogfood findings

A local qwen2.5-coder:7b-instruct run generated three baseline and five NIGHTMARE
candidates. Experimental lexical diversity was 0.7772 versus 0.4721, but 40 of
42 experimental claims remained unresolved. The model raised benchmark leakage,
subjective labels, lexical proxy failure, and external-validity concerns. It also
misused the claim grammar, producing narrow verifier failures. The run supports
the safeguards; it does not establish useful novelty.

## Failure analysis

The largest observed weakness is extraction: a verifier cannot detect a claim it
does not extract. Category classification is weak when a broad contradiction is
expected to carry a more specific label. Citation checks establish only supplied
ID presence. The framework does not verify source entailment, open-domain truth,
feasibility, or causal claims.

## Threats to validity

Cases are authored and template-derived, share vocabulary and evidence structure,
and are not sampled from real traffic. Split assignment follows template positions.
The confirmation partition is small. DreamValue labels were written with the
candidate pools and have not received independent review. The live audit used one
model, one prompt, one trial, unequal candidate counts, and confounded framing and
temperature. No provider cost was available; raw artifacts retain token counts
and latency.

## Conclusions

The infrastructure exposes failure instead of hiding it. The results do not
demonstrate general hallucination detection or a live useful-divergence advantage.
The held-out extraction collapse and unvalidated value judgments outweigh the
perfect confirmation result.

## Promotion decision

**HOLD**

HowlDream has a measurement foundation, but it has not earned deeper integration.
Milestone Three should collect independently authored natural-language cases and
blinded multi-rater labels, then compare equal-budget live baseline and DREAM
samples across several tasks.
