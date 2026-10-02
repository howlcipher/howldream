"""Measurement and interoperability regressions using finite fixtures only."""

import json
import subprocess
import sys

import pytest
from howl_provider_core import CommandConfig

from howldream.attribution import audit_attribution
from howldream.contracts import CandidateHandoff, ExplorationRequest
from howldream.engine import explore
from howldream.interop import exploration_from_candidate
from howldream.providers import RemoteCommandProvider, sampling_record
from howldream.schema import Evidence
from howldream.scoring import metrics
from howldream.validation import validate_artifact
from howldream.verification import extract, verify


def candidate():
    return CandidateHandoff(
        candidate_id="source-1",
        source_run_id="run-1",
        parent_request_id="run-1",
        objective="Museum queue",
        text="Proposal " + ("detail " * 1000),
        claims=[{"id": "claim-1", "kind": "HYPOTHESIS", "text": "Test queues"}],
        assumptions=["Visitors need accessible estimates"],
        unresolved_issues=["Observe wait time"],
        provenance={
            "producer_component": "howlcreate",
            "hard_constraints": ["No tracking"],
            "execution": {"model": "fixture", "mocked": True},
        },
    )


def test_sampling_requested_supported_applied():
    provider = RemoteCommandProvider(
        CommandConfig((sys.executable, "-c", "print('fixture')"), True)
    )
    controls = sampling_record(provider, 0.7, 42)
    assert controls["temperature"] == {"requested": 0.7, "supported": False, "applied": False}
    assert controls["seed"] == {"requested": 42, "supported": False, "applied": False}


def test_echo_does_not_count_as_support():
    evidence = [Evidence(id="s", text="X is true.", facts={"X": "true"})]
    claims = extract("FACT: X=true\nCALC: 2 + 3 = 5\nFACT: X=false\nUNKNOWN: Y", "c")
    checks = verify(claims, evidence)
    assert [c["status"] for c in checks] == ["ECHO", "SUPPORTED", "CONTRADICTED", "UNCERTAIN"]
    result = metrics([{"id": "c", "text": "fixture"}], checks)
    assert result["supported_count"] == 1
    assert result["echo_count"] == 1
    assert result["contradicted_count"] == 1
    assert result["uncertain_count"] == 1
    assert verify(extract("X IS true!", "c"), evidence)[0]["status"] == "ECHO"
    assert verify(extract("X is not true.", "c"), evidence)[0]["status"] != "ECHO"


def test_derived_support_remains_distinct():
    evidence = [Evidence(id="a", facts={"left": "2"}), Evidence(id="b", facts={"right": "3"})]
    derived = verify(extract("CALC: 2 + 3 = 5", "c"), evidence)
    assert derived[0]["status"] == "SUPPORTED"
    # Semantic derivation without an executable check remains uncertain.
    prose = verify(extract("Together A and B imply C.", "c"), evidence)
    assert prose[0]["status"] == "UNCERTAIN"


def test_bridge_and_deduplication(tmp_path):
    source = candidate()
    req = exploration_from_candidate(source)
    assert req.source_candidates[0].model_dump() == source.model_dump()
    assert req.parent_run_id == source.source_run_id
    assert req.constraints == ["No tracking"]
    req.budget.max_candidates = 6
    req.budget.max_calls = 9
    path, result = explore(req, tmp_path)
    encoded = result.model_dump_json()
    assert len(result.candidates) == 6
    assert encoded.count(source.text) == 1
    for generated in result.candidates:
        refs = generated.provenance.model_extra["source_candidate_refs"]
        assert refs[0]["candidate_id"] == source.candidate_id
        assert len(refs[0]["sha256"]) == 64
        assert "source_candidates" not in generated.provenance.model_extra
    assert len(encoded) < 80_000
    assert validate_artifact(path / "exploration_envelope.json")["valid"]


def test_bridge_cli(tmp_path):
    source = tmp_path / "candidate.json"
    source.write_text(candidate().model_dump_json())
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "howldream.cli",
            "explore",
            "--from-candidate",
            str(source),
            "--objective",
            "Attack assumptions",
            "--output",
            str(tmp_path / "runs"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["provenance"]["source_candidates"][0]["candidate_id"] == "source-1"
    assert result["provenance"]["source_candidates"][0]["claims"][0]["id"] == "claim-1"


@pytest.mark.parametrize("kind", ["candidate", "request", "evidence", "unknown"])
def test_polymorphic_validation(tmp_path, kind):
    value = {
        "candidate": candidate().model_dump(),
        "request": ExplorationRequest(request_id="r", objective="test").model_dump(),
        "evidence": [{"id": "s", "text": "test", "facts": {}}],
        "unknown": {"objective": "test"},
    }[kind]
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(value))
    if kind == "unknown":
        with pytest.raises(ValueError, match="UNKNOWN_ARTIFACT_TYPE"):
            validate_artifact(path)
    else:
        assert validate_artifact(path)["valid"]


def test_attribution_conflict():
    def entry(identifier, date, **kwargs):
        return {
            "id": identifier,
            "recorded_at": date,
            "concept": "Bounded repair retry",
            "source_ref": identifier + ".md",
            **kwargs,
        }

    value = {
        "schema_version": "howl.attribution_audit/v1",
        "baseline": [entry("baseline", "2026-10-01T10:00:00+00:00")],
        "howl_outputs": [entry("howl", "2026-10-01T11:00:00+00:00")],
        "decisions": [entry("decision", "2026-10-01T12:00:00+00:00")],
        "final_claims": [
            entry("report", "2026-10-01T13:00:00+00:00", classification="HOWL_ORIGINATED")
        ],
    }
    result = audit_attribution(value)
    assert result["conflicts"][0]["code"] == "ATTRIBUTION_CONFLICT"
    assert result["conflicts"][0]["recommended_classification"] == "PREEXISTING"
    value["baseline"][0]["recorded_at"] = "2026-10-01T12:00:00+00:00"
    assert audit_attribution(value)["conflicts"] == []


def test_provider_failure_retained(tmp_path):
    provider = RemoteCommandProvider(
        CommandConfig(
            (
                sys.executable,
                "-c",
                "import sys; print('session limit reached password=secret'); sys.exit(1)",
            ),
            True,
        )
    )
    source = candidate()
    req = exploration_from_candidate(source, remote=True)
    req.provider = {"kind": "command", "allow_remote": True}
    path, _ = explore(req, tmp_path, provider_override=provider)
    manifest = json.loads((path / "manifest.json").read_text())
    assert manifest["status"] == "PARTIAL"
    assert manifest["errors"][0]["failure"]["category"] == "SESSION_LIMIT"
    assert "secret" not in json.dumps(manifest)
    assert any("EXPERIMENT_CONTROL_NOT_APPLIED" in w for w in manifest["warnings"])


def test_http_failure_preserves_known_usage(monkeypatch):
    import io

    from howl_provider_core import ProviderError

    from howldream.providers import HTTPProvider
    from howldream.schema import ProviderConfig

    monkeypatch.setenv("HOWLDREAM_API_KEY", "fixture")
    provider = HTTPProvider(
        ProviderConfig(
            kind="openai_compatible", allow_remote=True, base_url="https://provider.example/v1"
        )
    )
    payload = {"model": "observed-model", "usage": {"prompt_tokens": 9}, "choices": []}
    provider.opener.open = lambda *a, **k: io.BytesIO(json.dumps(payload).encode())
    with pytest.raises(ProviderError) as error:
        provider.generate("fixture", "dream", 0, 0.7, 42)
    assert error.value.execution["usage"]["prompt_tokens"] == 9
    assert error.value.execution["model"] == "observed-model"
    assert error.value.failure["category"] == "MALFORMED_RESPONSE"


def test_attribution_missing_origin_keeps_timestamp_unknown():
    entry = {
        "id": "b",
        "recorded_at": "2026-10-01T10:00:00Z",
        "concept": "Bounded repair",
        "source_ref": "baseline.md",
    }
    claim = {
        **entry,
        "id": "d",
        "recorded_at": "2026-10-01T12:00:00Z",
        "classification": "HOWL_ORIGINATED",
    }
    result = audit_attribution(
        {
            "schema_version": "howl.attribution_audit/v1",
            "baseline": [entry],
            "howl_outputs": [],
            "decisions": [claim],
            "final_claims": [],
        }
    )
    assert result["conflicts"][0]["recommended_classification"] == "PREEXISTING"
    assert result["conflicts"][0]["howl_first_recorded_at"] is None
    assert result["unresolved"][0]["code"] == "MISSING_HOWL_ORIGIN_EVIDENCE"
