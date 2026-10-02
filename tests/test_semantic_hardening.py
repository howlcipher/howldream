"""Tests for natural language review, WAKE false-premise rejection, and metadata fidelity."""

import json
from pathlib import Path

from howl_provider_core import CommandConfig

from howldream.contracts import CandidateHandoff
from howldream.interop import review_candidate
from howldream.providers import RemoteCommandProvider
from howldream.schema import Evidence
from howldream.scoring import metrics, score_group
from howldream.verification import verify


def test_natural_language_candidate_review_extraction():
    """Verify natural prose candidate review extracts propositions and verifies them."""
    evidence = [
        Evidence(
            id="ev-01",
            text="The single-part put operations support payloads up to 5GB.",
            facts={"single_put_limit": "5GB", "kernel": "6.8"},
        )
    ]
    # Candidate text without line grammar prefixes
    candidate = CandidateHandoff(
        candidate_id="cand-natural-01",
        source_run_id="run-01",
        parent_request_id="req-01",
        objective="Verify object storage limits",
        text=(
            "Our staging ingress runs Linux kernel 6.8. "
            "The single-part put operations support payloads up to 5GB."
        ),
        claims=[],  # Empty claims: triggers natural language extraction
    )

    reviewed = review_candidate(candidate, evidence)

    assert len(reviewed.claims) >= 1
    # Check extraction provenance
    assert all(c.get("origin") == "NATURAL_EXTRACTED" for c in reviewed.claims)
    checks = reviewed.provenance.model_dump()["review"]["checks"]
    assert len(checks) >= 1
    # Supplied fact restatements remain reviewable but receive no independent support credit.
    assert any(c["status"] == "ECHO" for c in checks)


def test_structured_claims_candidate_review_preservation():
    """Verify review_candidate ingests and preserves structured claims from HowlCreate."""
    evidence = [
        Evidence(
            id="ev-02",
            text="Storage layer verified.",
            facts={"cas_latency": "12ms"},
        )
    ]
    structured_claims = [
        {
            "id": "cand-001/claim/mechanism",
            "candidate_id": "cand-001",
            "kind": "HYPOTHESIS",
            "text": "Fencing tokens with monotonic generation verification",
            "evidence_needs": ["Measure CAS latency under 100 concurrent nodes"],
            "status": "UNVERIFIED",
        },
        {
            "id": "cand-001/claim/assumption/1",
            "candidate_id": "cand-001",
            "kind": "ASSUMPTION",
            "text": "Storage layer supports atomic compare-and-swap",
            "status": "UNVERIFIED",
        },
    ]
    candidate = CandidateHandoff(
        candidate_id="cand-001",
        source_run_id="run-create-01",
        parent_request_id="req-create-01",
        objective="Design epoch lease barrier",
        text="Monotonic lease barrier using fencing tokens.",
        claims=structured_claims,
    )

    reviewed = review_candidate(candidate, evidence)

    assert len(reviewed.claims) == 2
    assert reviewed.claims[0]["id"] == "cand-001/claim/mechanism"
    assert reviewed.claims[0]["evidence_needs"] == [
        "Measure CAS latency under 100 concurrent nodes"
    ]
    assert reviewed.provenance.model_dump()["review"]["claims_origin"] == "SOURCE_STRUCTURED"


def test_wake_false_premise_rejection_credited():
    """Verify WAKE credits a candidate that explicitly rejects a false premise."""
    evidence = [
        Evidence(
            id="ev-s3",
            text="S3 documentation states single-part put limit is 5GB.",
            facts={"single_put_limit": "5GB"},
        )
    ]

    # Candidate 1: Explicitly rejects the false premise
    claims_cand1 = [
        {
            "id": "c1/claim/1",
            "candidate_id": "c1",
            "kind": "PREMISE",
            "text": "single_put_limit=500GB",
            "surface": (
                "We explicitly reject the false premise that single_put_limit is 500GB; "
                "the limit is 5GB."
            ),
            "modality": "denied",
            "status": "UNVERIFIED",
        }
    ]
    results_cand1 = verify(claims_cand1, evidence)
    assert len(results_cand1) == 1
    res1 = results_cand1[0]
    assert res1["evidence_status"] == "FALSE_PREMISE"
    assert res1["premise_stance"] == "PREMISE_REJECTED"
    assert res1["status"] == "SUPPORTED"
    assert res1.get("false_premise_rejected") is True
    assert "FALSE_PREMISE_ACCEPTANCE" not in res1["classifications"]

    # Candidate 2: Blindly accepts the false premise
    claims_cand2 = [
        {
            "id": "c2/claim/1",
            "candidate_id": "c2",
            "kind": "PREMISE",
            "text": "single_put_limit=500GB",
            "surface": "The single_put_limit allows uploads up to 500GB.",
            "modality": "asserted",
            "status": "UNVERIFIED",
        }
    ]
    results_cand2 = verify(claims_cand2, evidence)
    assert len(results_cand2) == 1
    res2 = results_cand2[0]
    assert res2["evidence_status"] == "FALSE_PREMISE"
    assert res2["premise_stance"] == "PREMISE_ACCEPTED"
    assert res2["status"] == "CONTRADICTED"
    assert "FALSE_PREMISE_ACCEPTANCE" in res2["classifications"]

    # Candidate 3: Leaves the false premise unresolved
    claims_cand3 = [
        {
            "id": "c3/claim/1",
            "candidate_id": "c3",
            "kind": "PREMISE",
            "text": "single_put_limit=500GB",
            "surface": "It is uncertain whether single_put_limit=500GB.",
            "modality": "uncertain",
            "status": "UNVERIFIED",
        }
    ]
    results_cand3 = verify(claims_cand3, evidence)
    assert len(results_cand3) == 1
    res3 = results_cand3[0]
    assert res3["evidence_status"] == "FALSE_PREMISE"
    assert res3["premise_stance"] == "PREMISE_UNRESOLVED"
    assert res3["status"] == "UNCERTAIN"
    assert "FALSE_PREMISE_ACCEPTANCE" not in res3["classifications"]

    # Score candidates and verify scoring / metrics attribution
    candidates = [
        {"id": "c1", "text": "IDEA: Safe multi-part chunking rejecting 500GB limit."},
        {"id": "c2", "text": "IDEA: Direct 500GB uploads relying on single-part put."},
    ]
    all_checks = results_cand1 + results_cand2
    scores = score_group(candidates, baseline=[], verification=all_checks)

    s1 = next(s for s in scores if s["candidate_id"] == "c1")
    s2 = next(s for s in scores if s["candidate_id"] == "c2")

    assert s1["false_premise_rejection_count"] == 1
    assert s1["decision"] == "INVESTIGATE"
    assert "successfully rejected 1 false premise" in s1["reason"]

    assert s2["false_premise_rejection_count"] == 0
    assert s2["decision"] == "REJECT"

    m = metrics(candidates, all_checks)
    assert m["false_premise_rejection_count"] == 1
    assert m["false_premise_acceptance_count"] == 1


def test_command_provider_usage_and_model_metadata(tmp_path: Path):
    """Verify RemoteCommandProvider preserves usage and model from CommandConfig."""
    config_data = {
        "argv": [
            "python3",
            "-c",
            (
                "import json; print(json.dumps({'result': 'IDEA: Test concept', "
                "'usage': {'input_tokens': 12, 'output_tokens': 8}}))"
            ),
        ],
        "remote": True,
        "model": "claude-sonnet-5-5",
        "adapter": "claude-json",
    }
    cfg_file = tmp_path / "command_config.json"
    cfg_file.write_text(json.dumps(config_data))

    provider = RemoteCommandProvider(CommandConfig.read(cfg_file))
    resp = provider.generate("Generate ideas", "dream", 0, 0.7, 42)

    assert resp.model == "unknown"
    assert resp.execution["requested_model"] == "claude-sonnet-5-5"
    assert resp.usage is not None
    assert resp.usage.get("input_tokens") == 12
    assert resp.usage.get("output_tokens") == 8
    assert resp.execution["requested_model"] == "claude-sonnet-5-5"


def test_natural_language_claim_extraction_edge_cases():
    """Verify claim extraction correctly classifies questions, suggestions, conditionals,
    negations, and uncertainty without treating them as asserted facts.
    """
    from howldream.verification import detect_modality, extract_natural, normalize_proposition

    # 1. "This may fail under clock skew." -> modality: possible
    assert detect_modality("This may fail under clock skew.") == "possible"
    claims_skew = extract_natural("This may fail under clock skew.", "cand-skew")
    assert len(claims_skew) == 1
    assert claims_skew[0]["modality"] == "possible"
    assert claims_skew[0]["status"] == "UNVERIFIED"

    # 2. "The service does not require wall-clock time." -> modality: denied
    assert detect_modality("The service does not require wall-clock time.") == "denied"
    claims_no_clock = extract_natural(
        "The service does not require wall-clock time.", "cand-noclock"
    )
    assert len(claims_no_clock) == 1
    assert claims_no_clock[0]["modality"] == "denied"

    # 3. "If network latency exceeds X, the approach could degrade." -> modality: conditional
    assert (
        detect_modality("If network latency exceeds X, the approach could degrade.")
        == "conditional"
    )

    # 4. "Consider using Redis." -> modality: suggestion, kind: SUGGESTION
    assert detect_modality("Consider using Redis.") == "suggestion"
    kind_sug, _text_sug, _ = normalize_proposition("Consider using Redis.")
    assert kind_sug == "SUGGESTION"

    # 5. "Redis guarantees this property." -> modality: asserted
    assert detect_modality("Redis guarantees this property.") == "asserted"

    # 6. "Does systemd behave this way?" -> modality: inquiry, kind: QUESTION
    assert detect_modality("Does systemd behave this way?") == "inquiry"
    kind_q, _text_q, _ = normalize_proposition("Does systemd behave this way?")
    assert kind_q == "QUESTION"


def test_dogfood_attribution_guide_taxonomy():
    """Verify dogfood_attribution_guide.md defines the complete 7-category taxonomy
    and the chronology precedence rule to prevent retroactive over-crediting.
    """
    guide_path = Path(__file__).resolve().parent.parent / "docs" / "dogfood_attribution_guide.md"
    assert guide_path.exists()
    content = guide_path.read_text(encoding="utf-8")

    # Assert all 7 canonical categories are explicitly present
    canonical_categories = [
        "PREEXISTING",
        "HOWL_ORIGINATED",
        "HOWL_REFINED",
        "HOWL_CHALLENGED",
        "HOWL_VALIDATED",
        "HOWL_INSPIRED_TEST",
        "HOWL_NO_EFFECT",
    ]
    for cat in canonical_categories:
        assert f"`{cat}`" in content, f"Missing taxonomy category: {cat}"

    # Assert Chronology Precedence Rule is documented
    assert "Chronology Precedence Rule" in content
    assert "MUST NOT later become `HOWL_ORIGINATED`" in content
