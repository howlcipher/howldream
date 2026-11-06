"""M2 Empirical Micro-Study Runner: 3-Candidate Verification

Validates the complete end-to-end pipeline:
howldream export-proof -> howlproof acquire -> howlproof evaluate --acquisition-store -> howldream import-proof

Candidate 1: Real gem release benchmark with verified acquisition & methodology quote.
Candidate 2: Cross-language/cross-tool cost efficiency and token reduction comparison (arithmetic + unverified marketing claim).
Candidate 3: Scoped documentation feature verification (Mutant README vs SKILL.md).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

MICRO_DIR = Path(__file__).resolve().parent
PROOF_PYTHON = "/run/media/howlcipher/tallgeese/dev/howlproof/.venv/bin/python"
DREAM_PYTHON = "/run/media/howlcipher/tallgeese/dev/howldream/.venv/bin/python"

RAW_DIR = MICRO_DIR / "inputs" / "raw"
STORE_DIR = MICRO_DIR / "acquisition_store"
BUNDLES_DIR = MICRO_DIR / "bundles"
PROOF_OUT_DIR = MICRO_DIR / "proof_out"
ASSESSMENTS_DIR = MICRO_DIR / "assessments"
RESULTS_DIR = MICRO_DIR / "results"
LOGS_DIR = MICRO_DIR / "logs"

COMMAND_LOG: list[dict] = []


def run_cmd(label: str, argv: list[str]) -> subprocess.CompletedProcess:
    res = subprocess.run(argv, capture_output=True, text=True, check=False)
    COMMAND_LOG.append({"label": label, "cmd": argv, "exit_code": res.returncode})
    (LOGS_DIR / f"{label}.stdout").write_text(res.stdout)
    (LOGS_DIR / f"{label}.stderr").write_text(res.stderr)
    # Proof evaluate returns 40 on INSUFFICIENT_EVIDENCE (the normal state without an acceptance contract)
    expected_exits = (0, 40) if label.startswith("evaluate_") else (0,)
    if res.returncode not in expected_exits:
        print(f"ERROR in {label} (exit {res.returncode}):\n{res.stderr}", file=sys.stderr)
    return res


def howlproof_acquire(label: str, file_path: Path, source_url: str) -> dict:
    cmd = [
        PROOF_PYTHON,
        "-m",
        "howlproof.cli",
        "acquire",
        "--store",
        str(STORE_DIR),
        "--file",
        str(file_path),
        "--source-url",
        source_url,
        "--operator",
        "microstudy-operator",
    ]
    res = run_cmd(f"acquire_{label}", cmd)
    assert res.returncode == 0, f"Acquire failed: {res.stderr}"
    return json.loads(res.stdout)


def build_candidate_01(acq_mame: dict) -> tuple[dict, list[dict]]:
    cand = {
        "candidate_id": "micro/01-mame-benchmark",
        "source_run_id": "microstudy-20261105",
        "parent_request_id": "microstudy-20261105",
        "objective": "Verify empirical benchmark measurement using primary source repository data and quoted methodology.",
        "text": "Claude Code mini-git benchmark: Ruby generation completes in approximately 73.1 seconds per run.",
        "claims": [
            {
                "id": "c01-ruby-generation-time",
                "candidate_id": "micro/01-mame-benchmark",
                "kind": "FACT",
                "text": "Ruby completes the mini-git generation benchmark in approximately 73.1 seconds.",
                "status": "UNVERIFIED",
                "category": "EMPIRICAL",
                "evidence_refs": ["mame_bench"],
                "check": {
                    "type": "fact_compare",
                    "fact": "ruby_time_seconds",
                    "op": "approx",
                    "expected": "73.1 s",
                    "tolerance": "0.1",
                    "nature": "measurement",
                },
                "subject_terms": ["Ruby", "Claude Code", "mini-git"],
                "checked_proposition": "The Claude Code mini-git benchmark reports Ruby completion time of approximately 73.1 seconds.",
                "scope": {
                    "artifact": "mame/ai-coding-lang-bench README.md",
                    "extent": "BENCHMARK_REPORT",
                },
            }
        ],
        "assumptions": [],
        "provenance": {
            "producer_component": "howldream",
            "observation_kind": "EXTERNALLY_OBSERVED",
            "origin": {"component": "microstudy-runner", "provider": None, "model": None},
            "created_at": "2026-11-05T20:00:00Z",
        },
    }
    evidence = [
        {
            "id": "mame_bench",
            "text": "",
            "facts": {
                "ruby_time_seconds": "73.1 s",
                "published_at": "2026-03-15T00:00:00Z",
            },
            "provenance": {
                "source_type": "EXTERNAL_OBSERVATION",
                "produced_by": "mame",
                "source_ref": "https://github.com/mame/ai-coding-lang-bench",
                "independent_of_implementation": True,
                "represents_observed_reality": True,
            },
            "acquisition": {
                "id": acq_mame["id"],
                "content_sha256": acq_mame["content_sha256"],
            },
            "methodology_quote": "We asked Claude Code (Opus 4.6) to implement a **mini-git** — a simplified version of Git",
        }
    ]
    return cand, evidence


def build_candidate_02(acq_mame: dict) -> tuple[dict, list[dict]]:
    cand = {
        "candidate_id": "micro/02-cross-lang-cost",
        "source_run_id": "microstudy-20261105",
        "parent_request_id": "microstudy-20261105",
        "objective": "Evaluate cross-language AI generation costs and token reduction claims.",
        "text": "Cross-language AI coding cost comparison and token reduction assertions.",
        "claims": [
            {
                "id": "c02-ruby-cost",
                "candidate_id": "micro/02-cross-lang-cost",
                "kind": "FACT",
                "text": "Claude Code average cost per run for Ruby is $0.36.",
                "status": "UNVERIFIED",
                "category": "EMPIRICAL",
                "evidence_refs": ["mame_bench"],
                "check": {
                    "type": "fact_compare",
                    "fact": "ruby_cost",
                    "op": "approx",
                    "expected": "$0.36",
                    "tolerance": "$0.01",
                    "nature": "measurement",
                },
                "subject_terms": ["Ruby", "cost"],
            },
            {
                "id": "c02-cost-reduction-arithmetic",
                "candidate_id": "micro/02-cross-lang-cost",
                "kind": "CALC",
                "text": "Ruby generation cost ($0.36) represents a 41.9% cost reduction relative to TypeScript ($0.62): (0.62 - 0.36) / 0.62 = 0.419.",
                "status": "UNVERIFIED",
                "category": "TECHNICAL",
                "evidence_refs": ["mame_bench"],
                "check": {
                    "type": "arithmetic",
                    "expression": "(0.62 - 0.36) / 0.62",
                    "op": "approx",
                    "expected": "0.419",
                    "tolerance": "0.001",
                },
            },
            {
                "id": "c02-placeholder-token-reduction",
                "candidate_id": "micro/02-cross-lang-cost",
                "kind": "FACT",
                "text": "Rubydex achieves a 65% prompt token reduction.",
                "status": "UNVERIFIED",
                "category": "EMPIRICAL",
                "evidence_refs": ["placeholder_bench"],
                "check": {
                    "type": "fact_compare",
                    "fact": "token_reduction_pct",
                    "op": "approx",
                    "expected": "65%",
                    "tolerance": "5%",
                },
                "subject_terms": ["Rubydex", "tokens"],
            },
        ],
        "assumptions": [],
        "provenance": {
            "producer_component": "howldream",
            "observation_kind": "EXTERNALLY_OBSERVED",
            "origin": {"component": "microstudy-runner", "provider": None, "model": None},
            "created_at": "2026-11-05T20:00:00Z",
        },
    }
    evidence = [
        {
            "id": "mame_bench",
            "text": "",
            "facts": {
                "ruby_cost": "$0.36",
                "published_at": "2026-03-15T00:00:00Z",
            },
            "provenance": {
                "source_type": "EXTERNAL_OBSERVATION",
                "produced_by": "mame",
                "source_ref": "https://github.com/mame/ai-coding-lang-bench",
                "independent_of_implementation": True,
                "represents_observed_reality": True,
            },
            "acquisition": {
                "id": acq_mame["id"],
                "content_sha256": acq_mame["content_sha256"],
            },
            "methodology_quote": "We asked Claude Code (Opus 4.6) to implement a **mini-git** — a simplified version of Git",
        },
        {
            "id": "placeholder_bench",
            "text": "",
            "facts": {
                "token_reduction_pct": "65%",
            },
            "provenance": {
                "source_type": "EXTERNAL_OBSERVATION",
                "produced_by": "unknown-vendor",
                "source_ref": "https://example.org/bench-token-study-a",
                "independent_of_implementation": True,
                "represents_observed_reality": True,
            },
        },
    ]
    return cand, evidence


def build_candidate_03(acq_readme: dict, acq_skill: dict) -> tuple[dict, list[dict]]:
    cand = {
        "candidate_id": "micro/03-scoped-mutant",
        "source_run_id": "microstudy-20261105",
        "parent_request_id": "microstudy-20261105",
        "objective": "Verify agent documentation in Mutant repository, preserving scoped refutation boundaries.",
        "text": "Mutant documentation features and agent integration availability.",
        "claims": [
            {
                "id": "c03-mutant-readme-agent",
                "candidate_id": "micro/03-scoped-mutant",
                "kind": "FACT",
                "text": "The Mutant README documents AI agent integration.",
                "status": "UNVERIFIED",
                "category": "EMPIRICAL",
                "evidence_refs": ["mutant_readme"],
                "check": {
                    "type": "text_presence",
                    "term": "agent",
                    "expect": "present",
                },
                "subject_terms": ["Mutant"],
                "checked_proposition": "The text of the Mutant README contains the word 'agent'",
                "scope": {
                    "artifact": "mbj/mutant README.md",
                    "extent": "SINGLE_FILE",
                },
            },
            {
                "id": "c03-mutant-skill-agent",
                "candidate_id": "micro/03-scoped-mutant",
                "kind": "FACT",
                "text": "The Mutant repository provides AI agent integration via SKILL.md.",
                "status": "UNVERIFIED",
                "category": "EMPIRICAL",
                "evidence_refs": ["mutant_skill"],
                "check": {
                    "type": "text_presence",
                    "term": "agent",
                    "expect": "present",
                },
                "subject_terms": ["Mutant"],
                "checked_proposition": "The text of Mutant SKILL.md contains the word 'agent'",
                "scope": {
                    "artifact": "mbj/mutant SKILL.md",
                    "extent": "SINGLE_FILE",
                },
            },
        ],
        "assumptions": [],
        "provenance": {
            "producer_component": "howldream",
            "observation_kind": "EXTERNALLY_OBSERVED",
            "origin": {"component": "microstudy-runner", "provider": None, "model": None},
            "created_at": "2026-11-05T20:00:00Z",
        },
    }
    evidence = [
        {
            "id": "mutant_readme",
            "text": "",
            "facts": {},
            "provenance": {
                "source_type": "EXTERNAL_OBSERVATION",
                "produced_by": "mbj/mutant",
                "source_ref": "https://github.com/mbj/mutant",
                "independent_of_implementation": True,
                "represents_observed_reality": True,
            },
            "acquisition": {
                "id": acq_readme["id"],
                "content_sha256": acq_readme["content_sha256"],
            },
        },
        {
            "id": "mutant_skill",
            "text": "",
            "facts": {},
            "provenance": {
                "source_type": "EXTERNAL_OBSERVATION",
                "produced_by": "mbj/mutant",
                "source_ref": "https://github.com/mbj/mutant",
                "independent_of_implementation": True,
                "represents_observed_reality": True,
            },
            "acquisition": {
                "id": acq_skill["id"],
                "content_sha256": acq_skill["content_sha256"],
            },
        },
    ]
    return cand, evidence


def main():
    print("=== M2 EMPIRICAL MICRO-STUDY: 3-CANDIDATE SUITE ===")
    # 1. Clean directories
    for d in (STORE_DIR, BUNDLES_DIR, PROOF_OUT_DIR, ASSESSMENTS_DIR, RESULTS_DIR, LOGS_DIR):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    # 2. Acquire source files into AcquisitionStore
    print("\n[Step 1] Acquiring source files into AcquisitionStore...")
    acq_mame = howlproof_acquire(
        "mame", RAW_DIR / "mame_README.md", "https://github.com/mame/ai-coding-lang-bench"
    )
    acq_readme = howlproof_acquire(
        "mutant_readme", RAW_DIR / "mutant_README.md", "https://github.com/mbj/mutant"
    )
    acq_skill = howlproof_acquire(
        "mutant_skill", RAW_DIR / "mutant_SKILL.md", "https://github.com/mbj/mutant"
    )
    print(f"  Acquired mame_bench: {acq_mame['id']} (sha256: {acq_mame['content_sha256'][:16]}...)")
    print(f"  Acquired mutant_readme: {acq_readme['id']} (sha256: {acq_readme['content_sha256'][:16]}...)")
    print(f"  Acquired mutant_skill: {acq_skill['id']} (sha256: {acq_skill['content_sha256'][:16]}...)")

    candidates = {
        "cand_01_mame": build_candidate_01(acq_mame),
        "cand_02_cross_cost": build_candidate_02(acq_mame),
        "cand_03_scoped_mutant": build_candidate_03(acq_readme, acq_skill),
    }

    summary: dict[str, dict] = {}

    for name, (cand_doc, ev_doc) in candidates.items():
        print(f"\n[Step 2] Processing {name} ({cand_doc['candidate_id']})...")
        cand_file = MICRO_DIR / "inputs" / f"{name}_candidate.json"
        ev_file = MICRO_DIR / "inputs" / f"{name}_evidence.json"
        cand_file.write_text(json.dumps(cand_doc, indent=2))
        ev_file.write_text(json.dumps(ev_doc, indent=2))

        # A. howldream export-proof
        bundle_dir = BUNDLES_DIR / name
        export_cmd = [
            DREAM_PYTHON,
            "-m",
            "howldream.cli",
            "export-proof",
            str(cand_file),
            "--evidence",
            str(ev_file),
            "--out",
            str(bundle_dir),
        ]
        res_exp = run_cmd(f"export_{name}", export_cmd)
        assert res_exp.returncode == 0, f"export-proof failed: {res_exp.stderr}"
        print(f"  -> Exported claim bundle to {bundle_dir.relative_to(MICRO_DIR)}")

        # B. howlproof evaluate
        proof_out = PROOF_OUT_DIR / name
        eval_cmd = [
            PROOF_PYTHON,
            "-m",
            "howlproof.cli",
            "evaluate",
            str(bundle_dir),
            "--profile",
            "research",
            "--acquisition-store",
            str(STORE_DIR),
            "--evidence-root",
            str(proof_out),
            "--json",
        ]
        res_eval = run_cmd(f"evaluate_{name}", eval_cmd)
        assert res_eval.returncode in (0, 40), f"evaluate failed with unexpected code {res_eval.returncode}: {res_eval.stderr}"
        proof_result = json.loads(res_eval.stdout)
        result_file = RESULTS_DIR / f"{name}_proof_result.json"
        result_file.write_text(json.dumps(proof_result, indent=2))
        print(f"  -> Evaluated with HowlProof: verdict={proof_result.get('verdict')}")

        # C. howldream import-proof
        assessment_file = ASSESSMENTS_DIR / f"{name}_assessment.json"
        import_cmd = [
            DREAM_PYTHON,
            "-m",
            "howldream.cli",
            "import-proof",
            "--bundle",
            str(bundle_dir),
            "--result",
            str(result_file),
            "--out",
            str(assessment_file),
        ]
        res_imp = run_cmd(f"import_{name}", import_cmd)
        assert res_imp.returncode == 0, f"import-proof failed: {res_imp.stderr}"
        assessment = json.loads(assessment_file.read_text())
        print(f"  -> Imported to HowlDream: disposition={assessment['disposition']}, confidence={assessment['confidence']}")
        print(f"     Reason: {assessment['reason']}")

        # Extract claim summary
        claims_summary = {}
        for row in assessment["evidence"]:
            if row.get("kind") == "proof_claim_result":
                cid = row["claim_id"]
                assurance = row.get("assurance") or {}
                claims_summary[cid] = {
                    "claim_status": row["claim_status"],
                    "check_outcome": row.get("check_outcome"),
                    "scope_limited": row.get("scope_limited"),
                    "source_origin": assurance.get("source_origin"),
                    "evidence_status": assurance.get("evidence_status"),
                    "corroboration": assurance.get("corroboration"),
                    "real_world_truth": assurance.get("real_world_truth"),
                }
            elif row.get("kind") == "proof_evidence_summary":
                summary_row = row

        summary[name] = {
            "candidate_id": cand_doc["candidate_id"],
            "proof_verdict": proof_result.get("verdict"),
            "dream_disposition": assessment["disposition"],
            "dream_confidence": assessment["confidence"],
            "dream_reason": assessment["reason"],
            "evidence_summary": summary_row,
            "claims": claims_summary,
        }

    # Save summary and command log
    (RESULTS_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    (LOGS_DIR / "commands.json").write_text(json.dumps(COMMAND_LOG, indent=2))

    print("\n=== VERIFICATION ASSERTIONS ===")

    # Candidate 1 Assertions:
    c1 = summary["cand_01_mame"]
    assert c1["dream_disposition"] == "INVESTIGATE"
    assert c1["dream_confidence"] == "MEDIUM"
    assert c1["evidence_summary"]["development_approval"] == "NOT_GRANTED"
    assert c1["evidence_summary"]["evidence_status"] == "ALL_CLAIMS_SOURCE_VERIFIED"
    c1_claim = c1["claims"]["c01-ruby-generation-time"]
    assert c1_claim["claim_status"] == "SUPPORTED"
    assert c1_claim["evidence_status"] in ("SOURCE_VERIFIED", "SOURCE_VERIFIED_SCOPED")
    assert c1_claim["source_origin"] == "OPERATOR_ATTESTED_FILE"
    assert c1_claim["real_world_truth"] == "UNRESOLVED"
    print("✓ Candidate 1 (Authentic Benchmark): Successfully verified against source & methodology quote; disposition INVESTIGATE, NO development approval.")

    # Candidate 2 Assertions:
    c2 = summary["cand_02_cross_cost"]
    assert c2["dream_disposition"] == "UNRESOLVED"
    assert c2["evidence_summary"]["evidence_status"] == "PARTIALLY_VERIFIED"
    assert c2["claims"]["c02-ruby-cost"]["claim_status"] == "SUPPORTED"
    assert c2["claims"]["c02-ruby-cost"]["evidence_status"] == "SOURCE_VERIFIED"
    assert c2["claims"]["c02-cost-reduction-arithmetic"]["claim_status"] == "SUPPORTED"
    assert c2["claims"]["c02-cost-reduction-arithmetic"]["evidence_status"] == "DETERMINISTIC_CHECK_ONLY"
    assert c2["claims"]["c02-placeholder-token-reduction"]["claim_status"] == "INCONCLUSIVE"
    assert c2["claims"]["c02-placeholder-token-reduction"]["source_origin"] == "PLACEHOLDER"
    print("✓ Candidate 2 (Cross-Lang Cost & Tokens): Arithmetic isolated, placeholder token claim kept INCONCLUSIVE; disposition UNRESOLVED.")

    # Candidate 3 Assertions:
    c3 = summary["cand_03_scoped_mutant"]
    assert c3["dream_disposition"] == "INVESTIGATE"  # Never REJECT or ACCEPT_FOR_DEVELOPMENT
    assert c3["claims"]["c03-mutant-readme-agent"]["claim_status"] == "REFUTED"
    assert c3["claims"]["c03-mutant-readme-agent"]["scope_limited"] is True
    assert c3["claims"]["c03-mutant-skill-agent"]["claim_status"] == "SUPPORTED"
    assert c3["claims"]["c03-mutant-skill-agent"]["scope_limited"] is True
    print("✓ Candidate 3 (Scoped Mutant Docs): Refutation preserved as scope-limited; does not reject candidate; disposition INVESTIGATE.")

    print("\nALL ASSERTIONS PASSED! Micro-study complete.")


if __name__ == "__main__":
    main()
