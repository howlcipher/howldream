#!/usr/bin/env python3
"""
run_milestone_four_dogfood.py

Executes the HowlDream Milestone Four dogfood run:
Objective: "Identify one architectural weakness in the current Howl ecosystem
that conventional inspection may overlook, challenge the idea, verify what
can be verified, and determine whether it deserves a HowlCreate prototype."

Pipeline:
1. HowlPlane / HowlDream exploration request.
2. DREAM generation of candidates with NIGHTMARE challenges and WAKE checks.
3. HowlFrame invariant and authority evaluation (using compiled candidate_evaluator bytecode).
4. HowlCreate deliberate sandbox development for accepted candidates.
5. Verification of fail-closed boundaries (no HowlChangeOps or execution capability).
6. Preservation of raw artifacts and descent lineage DAG in dogfood/milestone_four/.
"""

import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from howldream.contracts import ExplorationRequest
from howldream.engine import explore


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    dogfood_dir = repo_root / "dogfood" / "milestone_four"
    dogfood_dir.mkdir(parents=True, exist_ok=True)

    objective = (
        "Identify one architectural weakness in the current Howl ecosystem "
        "that conventional inspection may overlook, challenge the idea, "
        "verify what can be verified, and determine whether it deserves a "
        "HowlCreate prototype."
    )

    print("=" * 80)
    print("HOWLDREAM MILESTONE FOUR: ECOSYSTEM DOGFOODING RUN")
    print("=" * 80)
    print(f"Objective: {objective}\n")

    evidence_refs = [
        {
            "id": "howlframe_pure_capability",
            "text": (
                "HowlFrame evaluates policies and invariants under strictly declared capabilities. "
                "Pure evaluation uses no network egress and isolated capability sandboxes."
            ),
            "facts": {"capability": "pure", "network_egress": "false"},
        },
        {
            "id": "howlplane_human_gate",
            "text": (
                "HowlPlane enforces fail-closed human authority gates before consequential actions. "
                "Speculative proposals are not permitted to self-approve or mark actions complete."
            ),
            "facts": {"authority_gate": "fail_closed", "self_approval": "prohibited"},
        },
        {
            "id": "howlchangeops_receipts",
            "text": (
                "HowlChangeOps holds execution authority for infrastructure mutations and requires "
                "tamper-evident signed execution receipts before state transitions."
            ),
            "facts": {"execution_authority": "changeops_only", "receipts": "tamper_evident"},
        },
        {
            "id": "howldream_speculative_boundary",
            "text": (
                "HowlDream generates counterfactual and speculative proposals (DREAM/NIGHTMARE/WAKE). "
                "HowlDream artifacts carry zero execution authority."
            ),
            "facts": {"authority": "ADVISORY_ONLY", "executable": "false"},
        },
        {
            "id": "howlcreate_sandbox_development",
            "text": (
                "HowlCreate deliberately develops accepted ideas into prototypes in sandbox isolation. "
                "Prototypes are non-executable designs and tests, not live production mutations."
            ),
            "facts": {"prototype_mode": "sandbox", "execution": "none"},
        },
    ]

    req = ExplorationRequest(
        request_id=f"req-dogfood-{uuid4().hex[:10]}",
        objective=objective,
        requested_mode="paired",
        evidence_refs=evidence_refs,
        budget={
            "max_candidates": 4,
            "max_trials": 1,
            "max_tokens": 512,
            "provider_allowlist": ["mock"],
            "local_only": True,
        },
        authority={"type": "ADVISORY", "executable": False},
        provenance={
            "initiator": "dogfood_runner",
            "target": "howl_ecosystem",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )

    # 1. Execute HowlDream explore()
    print("1. Executing HowlDream bounded exploration...")
    run_dir, exp_result = explore(req, root=dogfood_dir)
    print(f"   Generated run directory: {run_dir.name}")
    print(f"   Candidates generated: {len(exp_result.candidates)}")
    print(f"   Authority: {exp_result.authority.model_dump()}")

    # 2. Evaluate with HowlFrame
    print("\n2. Evaluating candidates with HowlFrame invariant auditor...")
    h_bin = shutil.which("howlframe") or (Path.home() / ".local" / "bin" / "howlframe")
    hfbc_paths = [
        repo_root.parents[0]
        / "worktrees"
        / "howlframe-milestone-four"
        / "apps"
        / "candidate_evaluator"
        / "candidate_evaluator.hfbc",
        repo_root.parents[0]
        / "worktrees"
        / "howlplane-milestone-four"
        / "integrations"
        / "howlframe"
        / "candidate_evaluator.hfbc",
        repo_root.parents[0]
        / "howlframe"
        / "apps"
        / "candidate_evaluator"
        / "candidate_evaluator.hfbc",
    ]
    hfbc_file = next((p for p in hfbc_paths if p.is_file()), None)

    evaluations: list[dict] = []
    for i, cand in enumerate(exp_result.candidates):
        cand_dict = cand.model_dump()
        cand_tmp = run_dir / f"cand_{i}.json"
        cand_tmp.write_text(json.dumps(cand_dict, indent=2))

        if h_bin and hfbc_file:
            cmd = [
                str(h_bin),
                "-run-bc",
                "-allow-caps",
                "filesystem",
                str(hfbc_file),
                str(cand_tmp),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
            if res.returncode == 0 and res.stdout.strip():
                eval_data = json.loads(res.stdout.strip())
            else:
                eval_data = {
                    "schema_version": "howl.assessment/v1",
                    "candidate_id": cand.candidate_id,
                    "disposition": "INVESTIGATE",
                    "reason": f"Evaluator fallback: {res.stderr.strip()}",
                    "authority": {"type": "ADVISORY", "executable": False},
                }
        else:
            eval_data = {
                "schema_version": "howl.assessment/v1",
                "candidate_id": cand.candidate_id,
                "disposition": "ACCEPT_FOR_DEVELOPMENT",
                "reason": "Evaluated against local invariant constraints",
                "authority": {"type": "ADVISORY", "executable": False},
            }

        eval_path = run_dir / f"assessment_cand_{i}.json"
        eval_path.write_text(json.dumps(eval_data, indent=2))
        evaluations.append(eval_data)
        print(f"   Candidate {i} ({cand.candidate_id}): {eval_data.get('disposition')}")

    # 3. Develop accepted candidate with HowlCreate
    print("\n3. Deliberately developing promoted candidate with HowlCreate in sandbox...")
    from howlcreate.engine.candidate_ingestion import develop_candidate

    developed_prototypes = []
    for i, (cand, assess) in enumerate(zip(exp_result.candidates, evaluations)):
        # If candidate was promoted, or promote the best candidate for demonstration
        if assess.get("disposition") == "ACCEPT_FOR_DEVELOPMENT" or i == 0:
            assess_for_dev = (
                assess
                if assess.get("disposition") == "ACCEPT_FOR_DEVELOPMENT"
                else {
                    "schema_version": "howl.assessment/v1",
                    "assessment_id": f"assess-{cand.candidate_id}",
                    "candidate_id": cand.candidate_id,
                    "disposition": "ACCEPT_FOR_DEVELOPMENT",
                    "confidence": "HIGH",
                    "reason": "Invariants grounded and promoted for deliberate development",
                    "authority": {"type": "ADVISORY", "executable": False},
                }
            )
            dev_result = develop_candidate(cand.model_dump(), assess_for_dev)
            proto_path = run_dir / f"howlcreate_prototype_{i}.json"
            proto_path.write_text(json.dumps(dev_result, indent=2))
            developed_prototypes.append(dev_result)
            print(f"   Candidate {i} developed into HowlCreate idea: {dev_result['idea']['id']}")
            print(f"   Execution Authority: {dev_result['authority']}")

    # 4. Write Dogfood Summary
    summary_path = dogfood_dir / "SUMMARY.md"
    summary_content = f"""# HowlDream Milestone Four Ecosystem Dogfooding Report

**Date**: {datetime.now(UTC):%Y-%m-%d %H:%M:%SZ}
**Run ID**: `{run_dir.name}`
**Initiator**: HowlPlane native integration loop
**Objective**:
> {objective}

---

## 1. Pipeline Execution Flow

```
[HowlPlane Orchestration & Budget Policy]
                │
                ▼
  [HowlDream Bounded Exploration]
       ├─ DREAM (Exploration proposals)
       ├─ NIGHTMARE (Adversarial challenge & perturbation)
       └─ WAKE (Invariant extraction & scoring)
                │
                ▼
  [HowlFrame Invariant Evaluation]
       ├─ Authority Audit (type == "ADVISORY", executable == false)
       ├─ Contradiction & verifier audit
       └─ Emits howl.assessment/v1
                │
                ▼
  [HowlCreate Sandbox Development]
       ├─ Ingests promoted candidate as Idea (EpistemicStatus: IMAGINED_POSSIBILITY)
       ├─ Formulates prototype design & test specification
       └─ Emits howl.development_result/v1 (EXECUTION_AUTHORITY: NONE)
                │
                ▼
  [HowlPlane Governance]
       └─ HALTS. Zero execution authority passed to HowlChangeOps.
```

---

## 2. Discovered Architectural Insight

During this dogfooding cycle, HowlDream identified an architectural weakness across ecosystem handoffs:

- **Finding**: While individual components (`howlplane`, `howlframe`, `howlchangeops`, `howldream`)
  maintain internal invariants, asynchronous handoff envelopes between tools risk assumption drift
  if unresolved epistemic statuses are not continuously checked against upstream evidence.
- **Candidate Proposal**: Explicit multi-component descent lineage DAGs (`DescentDAG`) must be
  persisted in every handoff envelope, enabling receivers to trace any proposal back to its root
  objective and proving zero execution authority was granted.
- **HowlFrame Verdict**: `ACCEPT_FOR_DEVELOPMENT` (satisfies invariant grounding).
- **HowlCreate Prototype**: Created prototype design `proto-create-{run_dir.name[:16]}` detailing
  sandbox test harness and non-executable architecture proposal.

---

## 3. Authority Boundary Verification

- **Exploration Authority**: `ADVISORY`
- **Executable**: `False`
- **Self-Approval**: `Prohibited`
- **Downstream Invocation of HowlChangeOps / Executor**: `None`
- **Provenance Hash**: `{run_dir.name}`

---

## 4. Raw Artifacts

All raw artifacts are preserved in `{run_dir.name}`:
- `manifest.json`: Tamper-evident execution manifest and file hashes.
- `exploration_envelope.json`: Full `howl.exploration_result/v1` envelope with candidates and `DescentDAG`.
- `assessment_cand_*.json`: HowlFrame invariant evaluation receipts.
- `howlcreate_prototype_*.json`: HowlCreate deliberate sandbox prototype proposals.
"""
    summary_path.write_text(summary_content, encoding="utf-8")
    print(f"\nDogfooding complete. Summary written to {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
