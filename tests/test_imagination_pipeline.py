"""End-to-End AI Imagination & Anti-Reinvention Pipeline Test.

Verifies the complete cycle:
1. Dream explores an imaginative prompt.
2. An unoriginal idea (re-inventing the wheel) is caught by prior art research.
3. Dream tries again with avoidance context and dreams a novel, uncaptured alternative.
4. The novel candidate is exported via `export-proof`, with CALC propositions auto-derived
   into executable arithmetic checks.
5. Real HowlProof evaluates the claim bundle, proving out sound arithmetic and catching errors.
6. Dream imports the evaluation via `import-proof`, producing a truthful CandidateAssessment.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import ClassVar

from howldream.contracts import CandidateAssessment, ExplorationRequest
from howldream.engine import explore
from howldream.interop import export_candidate
from howldream.prior_art import MockPriorArt, PriorArtMatch
from howldream.proof_bridge import export_proof, import_proof
from howldream.providers import CAPABILITIES, Response


def proof_python() -> str:
    path = Path("/run/media/howlcipher/tallgeese/dev/howlproof/.venv/bin/python")
    if path.is_file():
        return str(path)
    return "python3"


def test_imagination_to_proof_end_to_end_lifecycle(tmp_path):
    # 1. Setup an imaginative provider that first generates an existing wheel,
    # then adapts upon retry to generate an unconventional idea with calculations.
    class ImaginativeProvider:
        capabilities: ClassVar[dict[str, bool]] = {**CAPABILITIES, "supports_temperature": True}

        def generate(self, prompt, condition, index, temperature, seed):
            if condition == "baseline":
                return Response(
                    "IDEA: Standard in-memory dictionary cache with fixed TTL\n"
                    "ASSUMPTION: RAM is sufficient for peak load",
                    "imagination-model-v1",
                )
            if "Do not reinvent existing wheels" in prompt or "Redis" in prompt:
                # Dream adapted: novel idea with verifiable math!
                return Response(
                    "IDEA: Kernel-bypass page slab with probabilistic compression\n"
                    "ASSUMPTION: Kernel bypass NIC driver is loaded\n"
                    "CALC: 64 * 8 = 512",
                    "imagination-model-v1",
                )
            else:
                # First dream attempt: re-invents an existing tool
                return Response(
                    "IDEA: Redis in-memory cache for session store\n"
                    "ASSUMPTION: Redis server instance is available",
                    "imagination-model-v1",
                )

    # 2. Prior art researcher knows about Redis
    researcher = MockPriorArt()
    researcher.add(
        "redis",
        PriorArtMatch(
            title="Redis In-Memory Data Store",
            source_ref="https://redis.io",
            summary="Pre-existing open-source in-memory key-value cache and database.",
            matched_terms=["redis", "cache"],
        ),
    )

    req = ExplorationRequest(
        request_id="imaginative-session-cache-001",
        objective="Design an ultra-low-latency distributed session cache with zero-copy serialization",
        budget={"max_candidates": 1, "max_calls": 5, "max_trials": 1},
    )

    # 3. Explore with prior art research enabled
    run_dir, result = explore(
        req, tmp_path / "runs", ImaginativeProvider(), prior_art_researcher=researcher
    )

    assert len(result.candidates) == 2

    # First candidate was flagged as reinventing the wheel
    reinvented = result.candidates[0]
    assert reinvented.status == "REJECTED"
    assert reinvented.provenance.model_extra.get("novelty_status") == "WHEEL_REINVENTED"
    assert "Redis" in (reinvented.provenance.model_extra.get("prior_art_match") or {}).get("title", "")

    # Second candidate was novel and uncaptured
    novel_candidate = result.candidates[1]
    assert novel_candidate.status in ("LOCALLY_VERIFIED", "UNRESOLVED", "CHALLENGED")
    assert novel_candidate.provenance.model_extra.get("novelty_status") == "UNCAPTURED_PRIOR_ART"
    assert "Kernel-bypass" in novel_candidate.text

    # 4. Export novel candidate as a CandidateHandoff
    handoff = export_candidate(run_dir, novel_candidate.candidate_id)
    assert handoff.claims, "Candidate must carry extracted claims"

    # 5. Export to Proof bundle via export-proof
    bundle_dir = tmp_path / "proof_bundle"
    bundle_manifest = export_proof(handoff, [], bundle_dir)
    assert (bundle_dir / "claims.json").is_file()

    # Verify auto-derived calculation check
    calc_claims = [c for c in bundle_manifest["claims"] if c.get("source_kind") == "CALC"]
    assert len(calc_claims) == 1
    calc_claim = calc_claims[0]
    assert calc_claim["category"] == "TECHNICAL"
    assert calc_claim["check"] == {
        "type": "arithmetic",
        "expression": "64 * 8",
        "op": "eq",
        "expected": "512",
    }

    # 6. Evaluate in HowlProof
    proof_py = proof_python()
    proof_out = tmp_path / "proof_evaluation"
    eval_proc = subprocess.run(
        [
            proof_py,
            "-m",
            "howlproof.cli",
            "evaluate",
            str(bundle_dir),
            "--profile",
            "research",
            "--evidence-root",
            str(proof_out),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    # HowlProof returns 40 on INSUFFICIENT_EVIDENCE (the natural state when no operator contract is supplied)
    assert eval_proc.returncode in (0, 40), f"Proof evaluate crashed: {eval_proc.stderr}"
    proof_result = json.loads(eval_proc.stdout)

    # Check that HowlProof verified the arithmetic
    claim_checks = {
        chk["check_id"]: chk
        for chk in proof_result["checks"]
        if chk["check_id"].startswith("research.claims.c")
    }
    assert claim_checks, "Proof must produce claim checks"

    # 7. Import Proof result back into HowlDream
    assessment = import_proof(bundle_dir, proof_result)
    assert isinstance(assessment, CandidateAssessment)
    assert assessment.candidate_id == novel_candidate.candidate_id

    # The proof claim results must record that the calculation was SUPPORTED
    proof_claims = [
        e for e in assessment.evidence if e.get("kind") == "proof_claim_result"
    ]
    supported_calc = next(
        (pc for pc in proof_claims if "64 * 8" in pc.get("explanation", "")), None
    )
    assert supported_calc is not None
    assert supported_calc["claim_status"] == "SUPPORTED"
    assert supported_calc["assurance"]["evidence_status"] == "DETERMINISTIC_CHECK_ONLY"

    # The overall candidate remains UNRESOLVED because the ungrounded assumptions
    # require real-world implementation testing
    assert assessment.disposition == "UNRESOLVED"
    assert assessment.confidence == "LOW"


def test_imagination_falsifies_flawed_calculation(tmp_path):
    # Verify that if an idea has a math mistake, Proof refutes it
    from howldream.contracts import CandidateHandoff
    from howldream.proof_bridge import export_proof, import_proof

    cand = CandidateHandoff(
        candidate_id="cand-flawed-math",
        source_run_id="run-test",
        parent_request_id="req-test",
        objective="Verify erroneous calculation",
        text="IDEA: Faulty scaling model\nCALC: 64 * 8 = 500",
        claims=[
            {"id": "c1", "kind": "IDEA", "text": "Faulty scaling model"},
            {"id": "c2", "kind": "CALC", "text": "64 * 8 = 500"},
        ],
    )
    bundle_dir = tmp_path / "flawed_bundle"
    export_proof(cand, [], bundle_dir)

    eval_proc = subprocess.run(
        [
            proof_python(),
            "-m",
            "howlproof.cli",
            "evaluate",
            str(bundle_dir),
            "--profile",
            "research",
            "--evidence-root",
            str(tmp_path / "proof_out"),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert eval_proc.returncode in (0, 40)
    proof_result = json.loads(eval_proc.stdout)

    assessment = import_proof(bundle_dir, proof_result)
    proof_claims = [
        e for e in assessment.evidence if e.get("kind") == "proof_claim_result"
    ]
    calc_result = next(pc for pc in proof_claims if pc["claim_id"] == "c2")
    assert calc_result["claim_status"] == "REFUTED"
    assert "does not hold" in calc_result["explanation"]
