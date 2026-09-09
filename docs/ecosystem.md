# Ecosystem audit and handoff contracts

Inspected 2026-09-08: local READMEs, HowlPlane CONTROL_PLANE and data-flow documents,
HowlWriter claim records, HowlCreate providers, installer manifest, Pages API metadata,
CI configurations, repository branches/status, and current GitHub metadata.

## Actual boundaries

| Component | Current role | Relationship to HowlDream |
| --- | --- | --- |
| HowlPlane | Operational AI engineering orchestration and authority gates | May evaluate an advisory run; no native adapter implemented |
| HowlCreate | Experimental creative search, mutation, challenge, concept lineage | May deliberately develop a candidate; no automatic import implemented |
| HowlFrame | Experimental language, compiler, capability-bounded VM | Future bounded verification programs, not a general factual-truth service |
| HowlChangeOps | Governed change execution, HowlFrame policy, human approvals | Sole relevant release boundary; no Dream-to-execution path |
| HowlRelay | Experimental async work-state and handoff system | May carry run pointers and unresolved work; not a Dream persistence dependency |
| HowlWriter | Writing, citation/provenance and verification workflows | May communicate reviewed conclusions; claims begin unverified, as in its domain model |
| Howl | Installer/lifecycle manager and canonical Pages hub | Dream is not registered in its default manifest |

HowlCreate already includes divergent exploration. The intended shorthand is:
HowlCreate invents intentionally; HowlDream explores speculatively through measured
experimental conditions. Neither output creates authority. HowlFrame's live README
and runtime contradict the broader "evidence/reasoning service" shorthand in HowlCreate's
README. This audit uses the actual language/runtime role; sibling copy is a future
documentation-sync candidate.

HowlBoard and HowlNotes are active external HowlFrame reference applications.
HowlBot is an external Discord policy dogfood application, not a core orchestration
component. `changeops` is a compatibility name and duplicate local checkout of
`howlchangeops`, not a separate current project. `ai_knowledge_library` is now the
HowlPlane knowledge subsystem. No inspected current component is declared deprecated
merely because of age. Repository existence alone is not a maturity guarantee.

## Handoff v1

Every completed WAKE analysis emits `handoff.json` with `schema: howldream.handoff/v1`, run_id,
`authority: NONE`, advisory outcome, unknown confidence, and candidate scores.
Consumers join candidate IDs to `candidates.jsonl`, `claims.jsonl`, and
`verification.jsonl`; sources live in `experiment.json`. This is a documented file
contract, not a claim of native sibling API compatibility.

Generation-only DREAM/NIGHTMARE handoffs contain schema, authority NONE, and
outcome UNVERIFIED; they do not yet contain candidate analysis or confidence.

For HowlCreate: pass objective, candidate text, evidence and unresolved assumptions,
novelty scorer type, and suggested next investigation. For HowlFrame: pass claims,
source records, contradiction checks, and requested additional verification to a
future explicitly authored bounded program. For HowlPlane: pass run pointer and
candidate set for its own policy evaluation. For HowlRelay: carry run pointer,
parent_run, status, and continuation questions. For HowlWriter: preserve distinction
between supplied evidence, generated speculation, and scoped check outcomes.

`INVESTIGATE` maps conceptually to deferred evaluation, `REJECT` to discarded proposals,
and `UNCERTAIN` to unresolved work. The suggested DEFER value is explicitly in the
`howldream.advisory` namespace; the inspected HowlPlane source did not establish the
prompt's proposed PURSUE/DEFER enumeration as a universal public contract. No speculative
mapping is represented as a working native integration.

## Installer decision

NOT YET INCLUDED IN DEFAULT INSTALLER. The embedded Howl manifest defines tested,
checksummed release combinations for core components. Adding a new experimental
component before a compatible release and install lifecycle test would overstate
support. Standalone wheel/source installation is available. No installer runtime
or profile behavior changes in this milestone.
