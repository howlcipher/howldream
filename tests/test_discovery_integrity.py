"""Discovery isolation, evidence honesty, claim-level checks and advisory diversity."""

import json
import subprocess
import sys

import pytest
from pydantic import ValidationError

from howldream.artifacts import load_run
from howldream.contracts import CandidateHandoff, ExplorationRequest
from howldream.discovery import analyze_discovery
from howldream.engine import explore, prompt_for, run
from howldream.evidence import (
    ClaimSupport,
    EvidenceProvenance,
    ReportEvidence,
    ValidationResult,
    audit_report,
    validation_requirements,
)
from howldream.interop import review_candidate
from howldream.providers import CAPABILITIES, Response
from howldream.schema import Evidence, Experiment, Generation
from howldream.scoring import score_group
from howldream.verification import extract, verify


class SubjectFixture:
    capabilities = CAPABILITIES

    def __init__(self):
        self.prompts = []

    def generate(self, prompt, condition, index, temperature, seed):
        self.prompts.append(prompt)
        families = ["roster options", "stadium accessibility", "travel logistics"]
        return Response(f"IDEA: MLB team {families[index % 3]}", "authored-fixture")


def test_discovery_ledger_is_verification_only(tmp_path):
    provider = SubjectFixture()
    request = ExplorationRequest(
        request_id="mlb",
        objective="MLB team",
        constraints=["No private tracking"],
        evidence_refs=[
            {
                "id": "ledger",
                "text": "Bullpen fatigue dominates operations",
                "facts": {"fatigue": "high"},
            }
        ],
        budget={"max_candidates": 3},
    )
    path, result = explore(request, tmp_path, provider)
    assert all("Bullpen fatigue" not in p and '"fatigue"' not in p for p in provider.prompts)
    assert all("No private tracking" in p for p in provider.prompts)
    assert all("distinct problem and opportunity families" in p for p in provider.prompts)
    assert result.evidence[0]["facts"]["fatigue"] == "high"
    assert result.provenance.model_extra["constraints"] == ["No private tracking"]
    assert result.candidates[0].provenance.model_extra["hard_constraints"] == [
        "No private tracking"
    ]
    assert load_run(path)["discovery"]["cluster_count"] == 3
    # The fixture proves prompt isolation and analysis, not model creativity.
    request.purpose = "development"
    provider.prompts.clear()
    explore(request, tmp_path, provider)
    assert all("Bullpen fatigue" in p for p in provider.prompts)


def test_verification_prompt_receives_ledger():
    exp = Experiment(
        schema_version=1,
        name="test",
        objective="review",
        purpose="verification",
        evidence=[Evidence(id="s", text="Observed artifact")],
    )
    assert "Observed artifact" in prompt_for(exp, "dream", 0)
    assert "seek falsification" in prompt_for(exp, "dream", 0)


@pytest.mark.parametrize(
    "control",
    [
        {"context_refs": ["x"]},
        {"risk_class": "HIGH"},
        {"constraints": [""]},
        {"unknown_control": True},
    ],
)
def test_ineffective_controls_rejected(control):
    with pytest.raises(ValidationError):
        ExplorationRequest(request_id="r", objective="x", **control)


def test_mutated_unsupported_control_revalidated(tmp_path):
    request = ExplorationRequest(request_id="r", objective="x")
    request.context_refs = ["must-not-resolve"]
    with pytest.raises(ValueError, match="UNSUPPORTED_CONTROL"):
        explore(request, tmp_path)


@pytest.mark.parametrize(
    "source_type",
    [
        "EXTERNAL_GROUND_TRUTH",
        "HISTORICAL_DATASET",
        "SYNTHETIC_FIXTURE",
        "OPERATOR_EXPECTATION",
        "MODEL_SELF_CONSISTENCY",
    ],
)
def test_validation_provenance_is_preserved(source_type):
    external = source_type in {"EXTERNAL_GROUND_TRUTH", "HISTORICAL_DATASET"}
    source = Evidence(
        id="s",
        facts={"x": "1"},
        provenance=EvidenceProvenance(
            source_type=source_type,
            produced_by="fixture author",
            source_ref="fixture://observations" if external else "fixture://authored",
            independent_of_implementation=external,
            represents_observed_reality=external,
        ),
    )
    check = verify(extract("FACT: x=1\nCITE: s", "c"), [source])
    assert check[0]["status"] == "ECHO"
    assert check[1]["check_scope"] == "CITATION_PRESENCE"
    assert check[1]["evidence_provenance"][0]["source_type"] == source_type


def validation(kind="SYNTHETIC_FIXTURE", **kwargs):
    external = kind == "HISTORICAL_DATASET"
    return ValidationResult(
        id="v",
        provenance=EvidenceProvenance(
            source_type=kind,
            produced_by="author",
            source_ref="fixture://archive",
            independent_of_implementation=external,
            represents_observed_reality=external,
        ),
        expected_value_origin="manually authored" if not external else "observed dataset",
        scope="specified scenarios only",
        outcome="PASS",
        artifact_ref="test-results.json",
        **kwargs,
    )


def test_operator_expected_value_is_not_ground_truth():
    with pytest.raises(ValidationError):
        EvidenceProvenance(source_type="OPERATOR_EXPECTATION", represents_observed_reality=True)
    with pytest.raises(ValidationError):
        EvidenceProvenance(source_type="EXTERNAL_GROUND_TRUTH")
    assert validation("OPERATOR_EXPECTATION").maturity()["level"] == 1
    assert validation("HISTORICAL_DATASET").maturity()["level"] == 2
    assert validation("HISTORICAL_DATASET", independent_benchmark=True).maturity()["level"] == 3
    assert (
        validation("HISTORICAL_DATASET", independent_benchmark=True, prospective=True).maturity()[
            "level"
        ]
        == 4
    )


@pytest.mark.parametrize(
    "claim,kind",
    [
        ("Historically proven and production-grade.", "SYNTHETIC_FIXTURE"),
        ("Statcast confirms this model is accurate.", "MODEL_SELF_CONSISTENCY"),
        ("This strategy improves wins.", "HISTORICAL_DATASET"),
        ("Historically validated.", "OPERATOR_EXPECTATION"),
    ],
)
def test_exaggerated_report_claim_flagged(claim, kind):
    ledger = ReportEvidence(
        validations=[validation(kind)], bindings=[ClaimSupport(claim=claim, validation_ids=["v"])]
    )
    audit = audit_report(claim, ledger)
    assert audit["findings"][0]["code"] == "CLAIM_EVIDENCE_MISMATCH"
    assert audit["findings"][0]["evidence_type"] == [kind]
    assert audit["findings"][0]["suggested_narrower_wording"]
    assert not audit_report("Passed controlled synthetic validation.", ledger)["findings"]


def test_unbound_empirical_claim_cannot_borrow_other_evidence():
    ledger = ReportEvidence(
        validations=[validation("HISTORICAL_DATASET", holdout=True, measured_metrics=["MAE"])]
    )
    assert audit_report("The forecast is accurate.", ledger)["findings"]
    claim = "The forecast is accurate."
    ledger.bindings = [ClaimSupport(claim=claim, validation_ids=["v"])]
    assert not audit_report(claim, ledger)["findings"]
    ledger.validations[0].outcome = "FAIL"
    assert audit_report(claim, ledger)["findings"]


def test_claim_level_mixed_wake_and_critical_gate():
    text = "IDEA: MLB team schedule\nCALC: 2 + 3 = 5\nFACT: x=1\nUNKNOWN: y\nCITE: missing"
    checks = verify(extract(text, "c"), [Evidence(id="s", facts={"x": "1"})])
    score = score_group([{"id": "c", "text": text}], [], checks, "MLB team")[0]
    assert score["decision"] == "INVESTIGATE"
    assert score["citation_error_count"] == 1
    assert score["claim_status_counts"]["SUPPORTED"] == 1
    assert score["claim_status_counts"]["ECHO"] == 1
    assert score["claim_status_counts"]["UNCERTAIN"] == 2
    assert (
        verify(extract("FACT: x=2", "c"), [Evidence(id="s", facts={"x": "1"})])[0]["status"]
        == "CONTRADICTED"
    )
    checks[-1]["critical"] = True
    assert (
        score_group([{"id": "c", "text": text}], [], checks, "MLB team")[0]["decision"] == "REJECT"
    )


def test_cluster_paraphrase_lineage_and_echo():
    candidates = [
        {"id": "a", "text": "IDEA: Schedule developer workload prediction\nASSUMPTION: x"},
        {"id": "b", "text": "IDEA: Forecast workloads for engineers schedules"},
        {"id": "c", "text": "IDEA: Stadium wheelchair accessibility routes"},
    ]
    analysis = analyze_discovery(candidates, [], "MLB team", [], [], ["novelty"])
    assert analysis["cluster_count"] == 2
    assert analysis["units"][1]["similar_to"] == "a/idea/1"
    start, end = analysis["units"][0]["source_span"]
    assert candidates[0]["text"][start:end] == analysis["units"][0]["text"]
    assert len(analysis["units"][0]["source_hash"]) == 64
    assert len(analysis["ranking"]) == 2
    echo = analyze_discovery(
        candidates[:2],
        [],
        "MLB team",
        [{"text": "Developer workload prediction scheduling", "facts": {}}],
        [],
        [],
    )
    assert echo["evidence_echo_ratio"] == 1.0
    assert echo["warnings"] == ["DISCOVERY_ANCHORING_HIGH"]


def test_diversity_memory_prompt_not_full_text(tmp_path):
    provider = SubjectFixture()
    request = ExplorationRequest(
        request_id="r",
        objective="MLB team",
        diversity_memory=True,
        explored_families=["ticketing"],
        budget={"max_candidates": 3},
    )
    explore(request, tmp_path, provider)
    assert all("ticketing" in p for p in provider.prompts)
    assert "roster" in provider.prompts[-1]
    assert "IDEA: MLB team roster options" not in provider.prompts[-1]
    assert "roster" not in provider.prompts[0]  # independent baseline control


def test_review_nested_claim_identity_and_provenance():
    candidate = CandidateHandoff(
        candidate_id="c",
        source_run_id="r",
        parent_request_id="q",
        objective="x",
        text="x",
        claims=[{"kind": "CALC", "text": "2 + 3 = 5"}],
    )
    reviewed = review_candidate(candidate, [])
    assert reviewed.claims[0]["candidate_id"] == "c"
    assert candidate.claims == [{"kind": "CALC", "text": "2 + 3 = 5"}]
    assert reviewed.provenance.model_extra["review"]["checks"][0]["status"] == "SUPPORTED"


def test_no_retention_discovery_does_not_leak(tmp_path):
    exp = Experiment(
        schema_version=1,
        name="private",
        objective="secretword",
        retain_text=False,
        generation=Generation(candidates=1),
    )
    path = run(exp, tmp_path, provider_override=SubjectFixture())
    stored = load_run(path)
    assert "units" not in stored["discovery"]
    assert "clusters" not in stored["discovery"]
    assert "secretword" not in "".join(p.read_text() for p in path.iterdir())


def test_audit_report_cli(tmp_path):
    report = tmp_path / "report.md"
    report.write_text("Historically proven.")
    ledger = tmp_path / "validation.json"
    ledger.write_text(ReportEvidence(validations=[validation()]).model_dump_json())
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "howldream.cli",
            "audit-report",
            str(report),
            "--validation",
            str(ledger),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 1
    assert json.loads(process.stdout)["findings"][0]["code"] == "CLAIM_EVIDENCE_MISMATCH"


def test_product_validation_checklists():
    assert "counterfactual limitations" in validation_requirements("decision")
    assert "holdout data" in validation_requirements("forecast")
    assert "known negatives" in validation_requirements("detector")
    assert "independent observed measurements" in validation_requirements("simulation")


def test_long_family_paraphrases_and_ledger_echo():
    candidates = [
        {
            "id": "a",
            "text": (
                "IDEA: Treat flaky tests as a statistical signal rather than a defect list, "
                "with Bayesian reliability estimates and a confidence score"
            ),
        },
        {
            "id": "b",
            "text": (
                "IDEA: Treat flaky tests as release-signal quality problems and publish "
                "a trust score based on rerun histories with quarantine"
            ),
        },
        {
            "id": "c",
            "text": (
                "IDEA: Trace infrastructure decisions back to their original owners "
                "and expired assumptions"
            ),
        },
    ]
    analysis = analyze_discovery(
        candidates,
        [],
        "Developer platform team",
        [
            {"text": "Flaky tests obscure release signals.", "facts": {}},
        ],
        [],
        [],
    )
    assert analysis["cluster_count"] == 2
    assert analysis["evidence_echo_ratio"] == pytest.approx(2 / 3)
    assert analysis["warnings"] == ["DISCOVERY_ANCHORING_HIGH"]
    assert analysis["units"][1]["similar_to"] == "a/idea/1"


def test_request_audit_metadata_preserved(tmp_path):
    request = ExplorationRequest(
        request_id="r", objective="subject", provenance={"operator_note": "declared context"}
    )
    _, result = explore(request, tmp_path, SubjectFixture())
    assert (
        result.provenance.model_extra["request_provenance"]["operator_note"] == "declared context"
    )
    assert result.provenance.model_extra["discovery_analysis"]["artifact"] == "discovery.json"


def test_clustering_does_not_join_generic_alternative_or_late_mentions():
    candidates = [
        {
            "id": "a",
            "text": (
                "IDEA: Unconventional alternative: invert golden paths "
                "into a marketplace of templates"
            ),
        },
        {
            "id": "b",
            "text": (
                "IDEA: Unconventional alternative: measure friction using latency "
                "across developer workflows"
            ),
        },
        {
            "id": "c",
            "text": (
                "IDEA: Build an environment cost budget that hibernates idle ephemeral environments"
            ),
        },
        {
            "id": "d",
            "text": (
                "IDEA: Test internal docs and runbooks for accuracy by regularly "
                "executing their sandboxed steps in ephemeral environments"
            ),
        },
    ]
    analysis = analyze_discovery(candidates, [], "platform", [], [], [])
    assert analysis["cluster_count"] == 4


def test_atomic_idea_export_preserves_parent_identity_and_uncertainty(tmp_path):
    from howldream.interop import export_candidate

    request = ExplorationRequest(request_id="r", objective="MLB team", constraints=["No tracking"])
    path, result = explore(request, tmp_path, SubjectFixture())
    unit_id = load_run(path)["discovery"]["units"][0]["id"]
    unit = export_candidate(path, unit_id)
    assert unit.candidate_id == unit_id
    assert unit.source_run_id == result.exploration_id
    assert unit.provenance.model_extra["parent_candidate_id"] == result.candidates[0].candidate_id
    assert unit.provenance.model_extra["source_unit"]["source_hash"]
    assert unit.provenance.model_extra["hard_constraints"] == ["No tracking"]
    assert unit.unresolved_issues == result.candidates[0].unresolved_issues
    assert len(unit.claims) == 1
    assert "verification" not in unit.provenance.model_extra
    assert result.candidates[0].candidate_id != unit.candidate_id


def test_unverified_tradeoff_is_not_a_candidate_contradiction(tmp_path):
    class TradeoffFixture(SubjectFixture):
        def generate(self, prompt, condition, index, temperature, seed):
            return Response(
                "IDEA: MLB team scheduling\nCONFLICT: autonomy versus standards\nCALC: 2 + 3 = 5",
                "authored-fixture",
            )

    _, result = explore(
        ExplorationRequest(request_id="r", objective="MLB team"), tmp_path, TradeoffFixture()
    )
    assert result.candidates[0].status == "UNRESOLVED"
    assert not result.candidates[0].contradictions
    assert "autonomy versus standards" in result.candidates[0].unresolved_issues


def test_experiment_discovery_cannot_bypass_selected_context_separation():
    with pytest.raises(ValueError, match="selected candidates require development"):
        Experiment(
            schema_version=1,
            name="x",
            objective="subject",
            purpose="discovery",
            speculative_candidates=[{"text": "detailed prior opportunity"}],
        )
