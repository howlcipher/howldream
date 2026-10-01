"""Provider boundary failures never erase completed observations."""

import http.client
import io
import json

import pytest

from howldream.artifacts import load_run
from howldream.engine import prompt_for, run
from howldream.providers import HTTPProvider
from howldream.schema import Experiment, ProviderConfig


@pytest.mark.parametrize(
    "body", [b"{}", b"{", b'{"choices":[]}', b'{"choices":[{"message":{"content":null}}]}']
)
def test_malformed_response(body, monkeypatch):
    monkeypatch.setenv("HOWLDREAM_API_KEY", "fixture-secret")
    provider = HTTPProvider(
        ProviderConfig(
            kind="openai_compatible",
            base_url="https://provider.example/v1",
            allow_remote=True,
        )
    )
    provider.opener.open = lambda *a, **k: io.BytesIO(body)
    with pytest.raises(ValueError):
        provider.generate("test", "dream", 0, 1.0, 0)


def test_truncated_http_response_preserves_run(tmp_path, monkeypatch):
    monkeypatch.setenv("HOWLDREAM_API_KEY", "fixture-secret")
    experiment = Experiment(
        schema_version=1,
        name="partial",
        objective="test",
        provider=ProviderConfig(
            kind="openai_compatible", base_url="https://provider.example/v1", allow_remote=True
        ),
    )
    provider = HTTPProvider(experiment.provider)
    count = 0

    def response(*args, **kwargs):
        nonlocal count
        count += 1
        if count == 1:
            body = {"choices": [{"message": {"content": "IDEA: test proposal"}}]}
            return io.BytesIO(json.dumps(body).encode())
        raise http.client.IncompleteRead(b"partial")

    provider.opener.open = response
    monkeypatch.setattr("howldream.engine.make_provider", lambda config: provider)
    artifacts = load_run(run(experiment, tmp_path))
    assert artifacts["manifest"]["status"] == "PARTIAL"
    assert len(artifacts["baseline"]) == 1
    assert len(artifacts["manifest"]["errors"]) == 8


def test_context_perturbation_leaves_original_evidence_intact():
    experiment = Experiment.model_validate(
        {
            "schema_version": 1,
            "name": "context",
            "objective": "test",
            "evidence": [{"id": "a", "facts": {"key": "yes"}}],
            "perturbations": [
                {"kind": "omit_context"},
                {"kind": "false_premise", "text": "key=no"},
            ],
        }
    )
    baseline = prompt_for(experiment, "baseline", 0)
    nightmare = prompt_for(experiment, "nightmare", 0)
    assert '"key": "yes"' in baseline and '"key": "yes"' not in nightmare
    assert "key=no" in nightmare and "key=no" not in baseline
    assert experiment.evidence[0].facts == {"key": "yes"}


@pytest.mark.parametrize(
    "url",
    ["http://example.com", "https://user:pass@example.com", "https://example.com?token=secret"],
)
def test_unsafe_endpoints_rejected(url):
    with pytest.raises(ValueError):
        HTTPProvider(ProviderConfig(kind="ollama", base_url=url, allow_remote=True))
