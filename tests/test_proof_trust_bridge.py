"""Dream <-> Proof under the M2 evidence trust model.

Ruby Renaissance v4 regression cases at the bridge: a research result must never read as
"independently verified fact" or as approval to build unless the evidence actually earns it.
The round trips run the real `howldream` and `howlproof` CLIs, offline.
"""

from __future__ import annotations

import json
import random
import subprocess
from pathlib import Path

import pytest
from test_proof_bridge import (
    candidate,
    dream,
    ev,
    proof_bin,
    proof_result,
    sclaim,
)

from howldream.contracts import CandidateAssessment
from howldream.proof_bridge import export_proof, import_proof

needs_proof = pytest.mark.skipif(proof_bin() is None, reason="howlproof CLI not installed")

DECLARED = {
    "source_type": "EXTERNAL_OBSERVATION",
    "produced_by": "benchmarking-lab-a",
    "source_ref": "https://example.org/bench-token-study-a",
    "independent_of_implementation": True,
    "represents_observed_reality": True,
}
REAL_REF = "https://railsatscale.com/rubydex-perf"
PAGE = (
    "<html>Rubydex benchmark. Method: 40 refactoring tasks against a ripgrep baseline. "
    "Rubydex cut prompt tokens by 63%.</html>"
)

ELIGIBLE = {
    "trust_model": "howl.evidence_trust/v1",
    "check_passed": True,
    "evidence_integrity": "ok",
    "source_origin": "OBSERVED_ACQUISITION",
    "claim_relevance": "STRUCTURAL_MATCH",
    "methodology": "RECORDED",
    "corroboration": "SINGLE_SOURCE",
    "corroborated": False,
    "real_world_eligible": True,
    "real_world_truth": "UNRESOLVED",
    "evidence_status": "SOURCE_VERIFIED",
}


def with_details(result, **per_claim):
    """Patch Proof's per-claim detail in a hand-built result."""
    for check in result["checks"]:
        detail = check.get("detail") or {}
        patch = per_claim.get(detail.get("claim_id"))
        if patch:
            detail.update(patch)
    return result


def three(tmp_path):
    cand = candidate(claims=[sclaim("c1", "a"), sclaim("c2", "b"), sclaim("c3", "c")])
    bundle = export_proof(cand, [], tmp_path / "bundle")
    return tmp_path / "bundle", bundle


# -- the disposition boundary ------------------------------------------------------------------


def test_fully_source_verified_support_is_not_approval_to_build(tmp_path):
    folder, bundle = three(tmp_path)
    result = with_details(
        proof_result(folder, bundle, dict.fromkeys(["c1", "c2", "c3"], "SUPPORTED")),
        **{cid: {"assurance": ELIGIBLE} for cid in ("c1", "c2", "c3")},
    )
    assessment = import_proof(folder, result)
    assert assessment.disposition == "INVESTIGATE"
    assert assessment.disposition != "ACCEPT_FOR_DEVELOPMENT"
    summary = next(e for e in assessment.evidence if e.get("kind") == "proof_evidence_summary")
    assert summary["development_approval"] == "NOT_GRANTED"
    assert summary["evidence_status"] == "ALL_CLAIMS_SOURCE_VERIFIED"
    assert "approval" in " ".join(assessment.limitations).lower()


def test_supported_without_an_assurance_record_is_treated_as_unverified(tmp_path):
    """A pre-M2 Proof result says SUPPORTED but cannot say on what basis."""
    folder, bundle = three(tmp_path)
    assessment = import_proof(
        folder, proof_result(folder, bundle, dict.fromkeys(["c1", "c2", "c3"], "SUPPORTED"))
    )
    assert assessment.disposition == "UNRESOLVED"
    summary = next(e for e in assessment.evidence if e.get("kind") == "proof_evidence_summary")
    assert summary["evidence_status"] == "UNVERIFIED"


def test_supported_only_against_synthetic_evidence_stays_unresolved(tmp_path):
    folder, bundle = three(tmp_path)
    synthetic = {
        **ELIGIBLE,
        "real_world_eligible": False,
        "evidence_status": "SYNTHETIC_FIXTURE_ONLY",
    }
    result = with_details(
        proof_result(folder, bundle, dict.fromkeys(["c1", "c2", "c3"], "SUPPORTED")),
        **{cid: {"assurance": synthetic} for cid in ("c1", "c2", "c3")},
    )
    assert import_proof(folder, result).disposition == "UNRESOLVED"


def test_one_unverified_claim_keeps_the_whole_bundle_unresolved(tmp_path):
    folder, bundle = three(tmp_path)
    weak = {**ELIGIBLE, "real_world_eligible": False, "evidence_status": "SUPPLIED_DATA_AGREES"}
    result = with_details(
        proof_result(folder, bundle, dict.fromkeys(["c1", "c2", "c3"], "SUPPORTED")),
        c1={"assurance": ELIGIBLE},
        c2={"assurance": ELIGIBLE},
        c3={"assurance": weak},
    )
    assert import_proof(folder, result).disposition == "UNRESOLVED"


def test_a_scope_limited_refutation_is_not_a_rejection(tmp_path):
    """Mutant: the README lacked the word; that is not 'Mutant has no agent integration'."""
    cand = candidate(claims=[sclaim("c1", "Mutant's README documents agent integration")])
    bundle = export_proof(cand, [], tmp_path / "bundle")
    folder = tmp_path / "bundle"
    result = with_details(
        proof_result(folder, bundle, {"c1": "REFUTED"}),
        c1={
            "scope_limited": True,
            "checked_proposition": "The text of Mutant's README mentions 'agent'",
            "broader_question": "NOT_EVALUATED",
            "also_found_in": ["skill"],
            "assurance": {
                **ELIGIBLE,
                "check_passed": False,
                "evidence_status": "SOURCE_VERIFIED_SCOPED",
            },
        },
    )
    assessment = import_proof(folder, result)
    assert assessment.disposition == "INVESTIGATE"
    row = next(e for e in assessment.evidence if e.get("kind") == "proof_claim_result")
    assert row["scope_limited"] is True and row["also_found_in"] == ["skill"]
    assert row["checked_proposition"].startswith("The text of Mutant's README")
    assert "scope" in assessment.reason.lower()


def test_an_unscoped_refutation_of_every_claim_still_rejects(tmp_path):
    folder, bundle = three(tmp_path)
    assert (
        import_proof(
            folder, proof_result(folder, bundle, dict.fromkeys(["c1", "c2", "c3"], "REFUTED"))
        ).disposition
        == "REJECT"
    )


def test_claim_rows_keep_the_full_assurance_record(tmp_path):
    folder, bundle = three(tmp_path)
    result = with_details(
        proof_result(folder, bundle, {"c1": "SUPPORTED", "c2": "INCONCLUSIVE", "c3": "REFUTED"}),
        c1={"assurance": ELIGIBLE, "check_outcome": "SUPPORTED"},
        c2={"check_outcome": "SUPPORTED"},
    )
    rows = {
        e["claim_id"]: e
        for e in import_proof(folder, result).evidence
        if e.get("kind") == "proof_claim_result"
    }
    assert rows["c1"]["assurance"] == ELIGIBLE
    assert (
        rows["c2"]["check_outcome"] == "SUPPORTED" and rows["c2"]["claim_status"] == "INCONCLUSIVE"
    )
    assert rows["c3"]["assurance"] is None  # absent stays absent; nothing is invented


def test_property_no_proof_result_can_yield_accept_for_development(tmp_path):
    folder, bundle = three(tmp_path)
    rng = random.Random(7)
    statuses = ["SUPPORTED", "REFUTED", "INCONCLUSIVE", "REQUIRES_EXTERNAL_VALIDATION", "ERROR"]
    for _ in range(150):
        chosen = {cid: rng.choice(statuses) for cid in ("c1", "c2", "c3")}
        result = proof_result(folder, bundle, chosen, integrity_ok=rng.choice([True, False]))
        patches = {
            cid: {
                "assurance": {**ELIGIBLE, "real_world_eligible": rng.choice([True, False])},
                "scope_limited": rng.choice([True, False]),
            }
            for cid in chosen
        }
        assessment = import_proof(folder, with_details(result, **patches))
        assert assessment.disposition != "ACCEPT_FOR_DEVELOPMENT", chosen


# -- export passthrough ------------------------------------------------------------------------


def test_export_carries_trust_fields_without_inventing_any(tmp_path):
    cand = candidate(
        claims=[
            sclaim(
                "c1",
                "Rubydex cut tokens by 63%",
                category="EMPIRICAL",
                subject_terms=["Rubydex"],
                checked_proposition="Source reports 63% fewer prompt tokens",
                scope={"artifact": "report", "extent": "SINGLE_FILE"},
                check={"type": "fact_compare", "fact": "t", "op": "eq", "expected": "63%"},
            ),
            sclaim("c2", "plain claim"),
        ]
    )
    evidence = [
        {
            **ev("e1", {"t": "63%"}),
            "acquisition": {"id": "acq-0123456789abcdef", "content_sha256": "a" * 64},
            "methodology_quote": "Method: 40 tasks",
        },
        ev("e2", {"t": "1%"}),
    ]
    bundle = export_proof(cand, evidence, tmp_path / "b")
    c1, c2 = bundle["claims"]
    assert c1["subject_terms"] == ["Rubydex"] and c1["scope"]["extent"] == "SINGLE_FILE"
    assert c1["checked_proposition"].startswith("Source reports")
    assert "subject_terms" not in c2 and "scope" not in c2 and "checked_proposition" not in c2
    e1, e2 = bundle["evidence"]
    assert e1["acquisition"]["id"] == "acq-0123456789abcdef"
    assert e1["methodology_quote"] == "Method: 40 tasks"
    assert "acquisition" not in e2 and "methodology_quote" not in e2


def test_malformed_trust_fields_are_rejected_at_export(tmp_path):
    cand = candidate(claims=[sclaim("c1", "x", subject_terms="Rubydex")])
    with pytest.raises(ValueError, match="subject_terms"):
        export_proof(cand, [], tmp_path / "b")


def test_a_bad_acquisition_pointer_is_rejected_at_export(tmp_path):
    cand = candidate(claims=[sclaim("c1", "x")])
    bad = {**ev("e1"), "acquisition": {"id": "../../etc/passwd", "content_sha256": "x"}}
    with pytest.raises(ValueError):
        export_proof(cand, [bad], tmp_path / "b")


# -- real round trips through both CLIs --------------------------------------------------------


def proof(*args: str, **kwargs):
    return subprocess.run(
        [proof_bin(), *args], capture_output=True, text=True, timeout=120, check=False, **kwargs
    )


def round_trip(tmp_path: Path, claims, evidence, store: Path | None = None, origin=None):
    cand = candidate(claims=claims)
    (tmp_path / "cand.json").write_text(cand.model_dump_json())
    (tmp_path / "ev.json").write_text(json.dumps(evidence))
    bundle = tmp_path / "bundle"
    done = dream(
        "export-proof", str(tmp_path / "cand.json"), "--evidence", str(tmp_path / "ev.json"),
        "--out", str(bundle),
    )  # fmt: skip
    assert done.returncode == 0, done.stderr
    args = [
        "evaluate",
        str(bundle),
        "--profile",
        "research",
        "--evidence-root",
        str(tmp_path / "p"),
    ]
    if store:
        args += ["--acquisition-store", str(store)]
    result = proof(*args, "--json")
    (tmp_path / "result.json").write_text(result.stdout)
    imported = dream(
        "import-proof", "--bundle", str(bundle), "--result", str(tmp_path / "result.json"),
        "--out", str(tmp_path / "assessment.json"),
    )  # fmt: skip
    assert imported.returncode == 0, imported.stderr
    assessment = CandidateAssessment.model_validate_json((tmp_path / "assessment.json").read_text())
    rows = {e["claim_id"]: e for e in assessment.evidence if e.get("kind") == "proof_claim_result"}
    return json.loads(result.stdout), assessment, rows, bundle


def token_claim(**extra):
    return sclaim(
        "tok",
        "Rubydex reduces prompt token usage by 63%",
        category="EMPIRICAL",
        subject_terms=["Rubydex"],
        check={"type": "fact_compare", "fact": "token_reduction", "op": "approx",
               "expected": "65%", "tolerance": "5%"},
        **extra,
    )  # fmt: skip


@needs_proof
def test_agy_placeholder_benchmark_never_becomes_verified_or_approved(tmp_path):
    evidence = [
        ev("study_a", {"token_reduction": "63%"}, provenance=DECLARED),
        ev("study_b", {"token_reduction": "64%"}, provenance={**DECLARED,
           "source_ref": "https://example.org/rubypack-size-bench"}),
    ]  # fmt: skip
    result, assessment, rows, _ = round_trip(tmp_path, [token_claim()], evidence)
    row = rows["tok"]
    assert row["claim_status"] == "INCONCLUSIVE"
    assert row["check_outcome"] == "SUPPORTED"  # the numbers agree; that is all it means
    assert row["assurance"]["source_origin"] == "PLACEHOLDER"
    assert row["assurance"]["real_world_eligible"] is False
    assert assessment.disposition == "UNRESOLVED"
    checks = {c["check_id"]: c for c in result["checks"]}
    assert checks["research.claims.c001"]["status"] != "VERIFIED"


@needs_proof
def test_genuine_acquired_source_gives_scoped_support_and_no_approval(tmp_path):
    page = tmp_path / "page.html"
    page.write_text(PAGE)
    store = tmp_path / "store"
    acquired = proof(
        "acquire", "--store", str(store), "--file", str(page), "--source-url", REAL_REF,
        "--operator", "tester",
    )  # fmt: skip
    assert acquired.returncode == 0, acquired.stderr
    record = json.loads(acquired.stdout)
    evidence = [
        {
            **ev(
                "study", {"token_reduction": "63%"}, provenance={**DECLARED, "source_ref": REAL_REF}
            ),
            "acquisition": {"id": record["id"], "content_sha256": record["content_sha256"]},
            "methodology_quote": "Method: 40 refactoring tasks against a ripgrep baseline.",
        }
    ]
    _, assessment, rows, bundle = round_trip(tmp_path, [token_claim()], evidence, store)
    row = rows["tok"]
    assert row["claim_status"] == "SUPPORTED"
    assert row["assurance"]["source_origin"] == "OPERATOR_ATTESTED_FILE"
    assert row["assurance"]["real_world_truth"] == "UNRESOLVED"
    assert row["assurance"]["corroborated"] is False
    assert assessment.disposition == "INVESTIGATE"  # never ACCEPT_FOR_DEVELOPMENT
    assert assessment.candidate_id == "run-1/cand-1" and row["claim_id"] == "tok"
    assert assessment.provenance.model_extra["bundle_sha256"]
    summary = next(e for e in assessment.evidence if e.get("kind") == "proof_evidence_summary")
    assert summary["development_approval"] == "NOT_GRANTED"
    assert (
        json.loads((bundle / "claims.json").read_text())["evidence"][0]["acquisition"]["id"]
        == record["id"]
    )


@needs_proof
def test_genuine_source_that_does_not_contain_the_numbers_cannot_support(tmp_path):
    page = tmp_path / "page.html"
    page.write_text("<html>Rubydex benchmark. Method: tasks. Rubydex cut tokens by 12%.</html>")
    store = tmp_path / "store"
    record = json.loads(
        proof(
            "acquire", "--store", str(store), "--file", str(page), "--source-url", REAL_REF
        ).stdout
    )
    evidence = [
        {
            **ev(
                "study", {"token_reduction": "63%"}, provenance={**DECLARED, "source_ref": REAL_REF}
            ),
            "acquisition": {"id": record["id"], "content_sha256": record["content_sha256"]},
        }
    ]
    _, _, rows, _ = round_trip(tmp_path, [token_claim()], evidence, store)
    assert rows["tok"]["claim_status"] == "INCONCLUSIVE"
    assert "not found in the acquired source" in rows["tok"]["explanation"]


@needs_proof
def test_mutant_readme_versus_skill_md_round_trip(tmp_path):
    store = tmp_path / "store"
    refs = {
        "readme": ("https://github.com/mbj/mutant", "Mutant is a mutation testing tool for Ruby."),
        "skill": (
            "https://github.com/mbj/mutant/blob/main/SKILL.md",
            "Mutant agent skill: workflow for coding agents.",
        ),
    }  # fmt: skip
    evidence = []
    for eid, (url, text) in refs.items():
        path = tmp_path / f"{eid}.txt"
        path.write_text(text)
        record = json.loads(
            proof("acquire", "--store", str(store), "--file", str(path), "--source-url", url).stdout
        )
        evidence.append(
            {
                **ev(eid, {}, provenance={**DECLARED, "source_ref": url}),
                "acquisition": {"id": record["id"], "content_sha256": record["content_sha256"]},
            }
        )
    claim = sclaim(
        "mut",
        "Mutant's README documents agent integration",
        category="EMPIRICAL",
        subject_terms=["Mutant"],
        checked_proposition="The text of Mutant's README mentions 'agent'",
        scope={"artifact": "README", "extent": "SINGLE_FILE"},
        evidence_refs=["readme"],
        check={"type": "text_presence", "term": "agent", "expect": "present"},
    )
    _, assessment, rows, _ = round_trip(tmp_path, [claim], evidence, store)
    row = rows["mut"]
    assert row["claim_status"] == "REFUTED" and row["scope_limited"] is True
    assert row["also_found_in"] == ["skill"]
    assert row["broader_question"] == "NOT_EVALUATED"
    assert assessment.disposition == "INVESTIGATE"  # NOT REJECT: the broader question is open


@needs_proof
def test_legacy_v1_evidence_round_trip_is_interpretable_not_authoritative(tmp_path):
    """A pre-M2 candidate: declared-independent evidence, no trust fields."""
    claim = sclaim(
        "old", "YJIT is 92% faster", category="EMPIRICAL",
        check={"type": "fact_compare", "fact": "speedup", "op": "approx",
               "expected": "92%", "tolerance": "1%"},
    )  # fmt: skip
    evidence = [ev("bench", {"speedup": "92%"}, provenance={**DECLARED, "source_ref": REAL_REF})]
    _, assessment, rows, _ = round_trip(tmp_path, [claim], evidence)
    assert rows["old"]["claim_status"] == "INCONCLUSIVE"
    assert rows["old"]["check_outcome"] == "SUPPORTED"
    assert rows["old"]["assurance"]["source_origin"] == "CLAIMED_ONLY"
    assert assessment.disposition == "UNRESOLVED"
