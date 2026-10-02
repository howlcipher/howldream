import json
from unittest.mock import patch

import pytest
from howl_provider_core import ProviderError

from howldream.artifacts import load_run
from howldream.contracts import CandidateHandoff, ExplorationRequest
from howldream.engine import explore, run
from howldream.interop import export_candidate, review_candidate
from howldream.providers import CAPABILITIES, HTTPProvider, MockProvider, Response, make_provider
from howldream.schema import Evidence, Experiment, ProviderConfig


def test_forbidden_local_selection(monkeypatch):
    monkeypatch.setenv("HOWL_FORBID_LOCAL_INFERENCE", "1")
    with patch("socket.create_connection", side_effect=AssertionError("no transport")):
        with pytest.raises(ProviderError):
            make_provider(ProviderConfig(kind="ollama", allow_local_inference=True))
        with pytest.raises(ProviderError):
            make_provider(ProviderConfig(kind="openai_compatible", base_url="https://localhost"))


def test_policy_rechecked_for_cached_provider(monkeypatch):
    monkeypatch.setenv("HOWLDREAM_API_KEY", "fixture-secret")
    provider = HTTPProvider(
        ProviderConfig(
            kind="openai_compatible", base_url="https://provider.example/v1", allow_remote=True
        )
    )
    # Represent an old cached local adapter without ever lifting the prohibition.
    provider.config = ProviderConfig(kind="ollama", allow_local_inference=True)
    provider.base = "http://127.0.0.1:11434"
    provider.opener.open = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP"))
    monkeypatch.setenv("HOWL_FORBID_LOCAL_INFERENCE", "1")
    with pytest.raises(ProviderError):
        provider.generate("test", "dream", 0, 1, 0)


def test_unsupported_fact_never_promoted(tmp_path, monkeypatch):
    class Fake:
        capabilities = CAPABILITIES

        def generate(self, *args):
            return Response("IDEA: test parser\nFACT: unsupported=true", "fake")

    monkeypatch.setattr("howldream.engine.make_provider", lambda _: Fake())
    _, result = explore(ExplorationRequest(request_id="test", objective="parser"), tmp_path)
    assert all(x.status != "LOCALLY_VERIFIED" for x in result.candidates)
    assert all(x.verified_constraints == [] for x in result.candidates)
    assert all(x.trust == "UNVERIFIED" for x in result.candidates)


def test_zero_budget_has_no_dispatch(tmp_path, monkeypatch):
    provider = MockProvider()
    monkeypatch.setattr(provider, "generate", lambda *args: (_ for _ in ()).throw(AssertionError()))
    path = run(
        Experiment(schema_version=1, name="zero", objective="test", max_calls=0),
        tmp_path,
        provider_override=provider,
    )
    manifest = load_run(path)["manifest"]
    assert manifest["call_count"] == 0
    assert manifest["stop_reason"] == "BUDGET_EXHAUSTED"
    assert manifest["status"] == "PARTIAL"


def test_run_export_and_review_preserve_source(tmp_path):
    path = run(Experiment(schema_version=1, name="export", objective="test parser"), tmp_path)
    row = load_run(path)["candidates"][0]
    candidate = export_candidate(path, row["id"])
    assert candidate.candidate_id == row["id"]
    assert candidate.provenance.model_dump()["execution"]["mocked"] is True
    reviewed = review_candidate(candidate, [Evidence(id="ledger", facts={"key": "yes"})])
    assert reviewed.candidate_id == candidate.candidate_id
    assert reviewed.provenance.model_dump()["source_candidate"] == candidate.model_dump()
    assert reviewed.claims == candidate.claims
    assert reviewed.authority.executable is False


def test_create_dream_contract_roundtrip(tmp_path):
    pytest.importorskip("howlcreate")
    from howlcreate.engine.pipeline import CreativePipeline, PipelineConfig
    from howlcreate.formatting.dream import export_dream_candidate
    from howlcreate.providers.deterministic import DeterministicProvider

    record = CreativePipeline(PipelineConfig(save_run=False)).execute(
        "Design a parser", DeterministicProvider()
    )
    idea = record.get_finalists()[0]
    candidate = CandidateHandoff.model_validate(export_dream_candidate(record, idea.id))
    request = ExplorationRequest(
        request_id="interop", objective=record.problem, source_candidates=[candidate]
    )
    path, result = explore(request, tmp_path)
    assert (
        result.candidates[0].provenance.model_dump()["source_candidate_refs"][0]["candidate_id"]
        == idea.id
    )
    artifact = load_run(path)
    prompt = json.loads(artifact["candidates"][0]["prompt"].split("\n")[-1])
    assert prompt["unverified_candidate_context"][0]["candidate_id"] == idea.id
    assert not any(e["id"] == idea.id for e in artifact["experiment"]["evidence"])
