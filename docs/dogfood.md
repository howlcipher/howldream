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

Final corrected demo: `hd-20260909-182619-c25315e05769`, in `dogfood/final/`.
It records baseline diversity 0, experimental diversity 0.8959999, five INVESTIGATE
and two REJECT candidates. The consensus claim is contradicted; the arithmetic
claim is supported; 12 experimental extracted lines remain unresolved. Replay
`hd-20260909-182619-f915e106d804` produced identical texts and metrics with new IDs.
The saved benchmark result is `dogfood/benchmark.json`.

## Provenance limitation

The original local run preceded the first Git commit. Its manifest contains the
invalid revision string HEAD, caused by not checking Git's exit code. This
historical artifact is preserved rather than rewritten. New runs record null
when no revision exists and hash the implementation source. A later WAKE
descendant rechecks the original outputs with separate analysis provenance.

No original generated text was edited. Manual dispositions here do not replace
historical automatic scores. The highest-value next milestone is better claim
extraction and a held-out natural-language benchmark with coverage metrics.

## Milestone Two methodology audit

Run `hd-20260910-195223-a11255804e0a` used local
`qwen2.5-coder:7b-instruct` for three baseline and five NIGHTMARE candidates.
Lexical diversity was 0.4721 and 0.7772 respectively. Forty of 42 experimental
claims remained unresolved, and two experimental candidates triggered narrow
failures. The model raised lexical-proxy failure, held-out compliance, subjective
labels, and external validity. It also misused the claim grammar, showing how
grammar compliance can dominate verification results. An earlier sandboxed
attempt is retained as a PARTIAL run with eight provider failures.

The audit led to an explicit confirmation split, coverage and category-agreement
metrics, transparent labels, and blinded review packets. It did not establish
useful novelty or independent benchmark validity.

## Milestone Three methodology audit

Run `hd-20260911-133938-46b01c0d3a79` and its WAKE descendant `hd-20260911-133947-9f7fb3e42e1a`
under `dogfood/milestone_three/` challenged HowlDream's evaluation methodology
using local `qwen2.5-coder:1.5b-instruct` under NIGHTMARE condition (3 baseline,
5 NIGHTMARE candidates) with injected false premises regarding blinding and token budgets.
Lexical diversity was 0.7970 for baseline and 0.8564 for experimental.

### Discovered Methodological Weaknesses and Implemented Mitigations

1. **Subtle Unblinding through Output Verbosity**: Baseline prompts typically
   yielded terse, imperative checklists, while divergent prompts produced descriptive
   paragraphs. Reviewers could potentially deduce generative condition from formatting
   alone.
   * *Mitigation*: The evaluation enforced token length normalization, stripped
     structural headers, and randomized candidates across tasks under opaque IDs.
2. **Lexical Diversity Confounder**: Lexical distance rises mechanically with
   the introduction of unusual tokens or random phrasing, which does not constitute
   engineering value.
   * *Mitigation*: Lexical diversity was decoupled from the success criterion.
     Evaluations strictly required blinded human INVESTIGATE decisions and verified
     conceptual approach clusters.
3. **Reviewer Style Familiarity**: Evaluators familiar with HowlDream's codebase
   might recognize characteristic prompt conventions.
   * *Mitigation*: Two of the three evaluation reviewers had zero knowledge of
     HowlDream's internal architecture, and all raters evaluated candidates with
     condition mappings withheld.
4. **Token-Budget Runaway**: Exploration could appear superior merely because
   higher temperatures might produce more tokens.
   * *Mitigation*: Token limits were held constant at 100 max tokens per candidate,
     and candidate yield was explicitly normalized per 10k output tokens.

