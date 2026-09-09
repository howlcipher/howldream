# Dogfood findings

## Question and original run

Generate unconventional methods for detecting hallucination that do not depend
exclusively on asking one LLM to judge another LLM.

Original local run: hd-20260909-005406-84dc8032d590, retained under dogfood/local/.
Provider: local Ollama, qwen2.5-coder:7b-instruct. Three baseline candidates at
temperature 0.2; five DREAM candidates at 1.2. The experimental condition also
injected a premise to challenge: model consensus proves truth. One trial,
no retries, no paid or remote inference.

| Measurement | Baseline | DREAM |
| --- | ---: | ---: |
| Outputs | 3 | 5 |
| Exact unique outputs | 3 | 5 |
| Mean pairwise token Jaccard distance | 0.582427 | 0.850957 |
| Detected known-check failures | 0 | 0 |
| Unresolved extracted lines | 6 | 9 |

This supports greater lexical diversity in this single tested condition.
Prompt framing, temperature, and premise challenge changed together. It does not
isolate causality, demonstrate semantic novelty, or establish model-wide performance.
None of these proposals supplied a factual ledger claim that could establish
feasibility. Zero detected failures therefore means very little by itself.

## Challenge and engineering review

The automatic relevance heuristic marked all five proposals INVESTIGATE. The
following is separate engineering judgment after reading the actual outputs:

| Index | Proposal | Disposition | Challenge and next step |
| --- | --- | --- | --- |
| 0 | Neural activity during dream-like states | REJECT for milestone one | Requires unavailable instrumentation; no exposed signal establishes feasibility |
| 1 | Compare computational complexity across models | UNCERTAIN | Architecture and workload confound complexity; no signal definition or validation |
| 2 | Linguistic anomalies and unusual word usage | UNCERTAIN | Fluent fabrication and unusual correct prose are counterexamples; needs held-out data |
| 3 | Arithmetic challenge | INVESTIGATE | Independent witnesses check numerical equality; reject the assumption that LLM arithmetic is reliable |
| 4 | Cross-model consistency and context | UNCERTAIN | Disagreement can guide investigation; consensus cannot verify truth |

The arithmetic proposal did not invent exact arithmetic checking; a checker
already existed here. It reinforced a useful bounded direction. Independent code
review then found a rounding defect: an incorrect large product was marked
SUPPORTED. A failing regression reproduced it; the checker now uses exact rational
arithmetic. This is a reliability improvement, not a claim that the model found
the code defect.

The run also exposed poor visibility of verification coverage. Reports now show
unresolved claim counts beside detected failures. This prevents zero detections
from concealing that the verifier could not assess generated assumptions.

## Authored demonstration

examples/self_detection.yaml exercises seven authored mock ideas against three
identical baseline responses. The consensus-guarantee claim is contradicted by
the supplied ledger. The first run incorrectly marked an unrelated carousel
INVESTIGATE because the common word "for" overlapped the objective. A failing
regression reproduced this; relevance now excludes common function words.
New runs reject the unrelated carousel for lexical irrelevance;
other engineering proposals remain investigation candidates. NIGHTMARE injects
an unsupported fixture claim and perturbs context. These demonstrate framework
behavior, not AI discoveries or empirical model perturbation effects.

## Provenance limitation

The original local run preceded the first Git commit. Its manifest contains the
invalid revision string HEAD, caused by not checking Git's exit code. This
historical artifact is preserved rather than rewritten. New runs record null
when no revision exists and hash the implementation source. A later WAKE
descendant rechecks the original outputs with separate analysis provenance.

No original generated text was edited. Manual dispositions here do not replace
historical automatic scores. The highest-value next milestone is better claim
extraction and a held-out natural-language benchmark with coverage metrics.
