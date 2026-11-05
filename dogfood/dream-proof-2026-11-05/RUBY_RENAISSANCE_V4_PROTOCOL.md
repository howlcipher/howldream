# Ruby Renaissance v4: protocol (prepared, not run)

**Baseline** the November 2026 Claude and AGY investigations (archives preserved, unmodified).
**Treatment** independent Claude and AGY runs using the Dream to Proof workflow
(`docs/dream_to_proof.md`). Same scope, opportunity scorecards, evidence requirements and
research questions.

Independence: Claude and AGY work in separate checkouts; neither reads the other's v4
findings until both runs are frozen (hash the final archive, then exchange).

Record separately, per run:

1. ideas HowlDream actually generated (`MODEL_GENERATED`) versus externally supplied (`EXTERNAL_AUTHORED`)
2. claims passed to HowlProof (`claims` in `export-proof` output)
3. claims substantively SUPPORTED or REFUTED, and claims left INCONCLUSIVE / REQUIRES_EXTERNAL_VALIDATION / ERROR
4. manual interventions (hand-authored checks, split compound claims, evidence transcription)
5. unsupported claims that still entered the final report (diff report assertions against assessments)
6. useful information produced and remaining failures

Do not count more SUPPORTED claims as improvement unless each verdict is defensible: re-fetch
primary sources, mark evidence independent only when it is, and review a sample by hand.
Judge the change by evidence quality, translation effort, preserved uncertainty, and the
reliability of the final decision, not by verdict counts.
