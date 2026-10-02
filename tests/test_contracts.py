"""Observable trust, experiment, and reproducibility contracts."""

import json
import subprocess
import sys

import pytest
from pydantic import ValidationError

from howldream import __version__
from howldream.artifacts import load_run, redact, scrub
from howldream.benchmark import benchmark, load_dataset
from howldream.engine import replay, run, wake
from howldream.providers import MockProvider, make_provider
from howldream.schema import Experiment
from howldream.scoring import score_group
from howldream.verification import extract, verify


def spec(**updates):
    data = {
        "schema_version": 1,
        "name": "test",
        "objective": "Detect hallucination",
        "evidence": [{"id": "s1", "facts": {"sky": "blue"}}],
    }
    data.update(updates)
    return Experiment.model_validate(data)


@pytest.mark.parametrize(
    "update",
    [
        {"schema_version": 2},
        {"schema_version": True},
        {"schema_version": 1.0},
        {"surprise": True},
        {"trials": 0},
        {"trials": True},
        {"generation": {"candidates": -1}},
        {"provider": {"kind": "imaginary"}},
        {"generation": {"temperature": "hot"}},
        {"evidence": [{"id": "x", "extra": 1}]},
    ],
)
def test_schema_rejects_invalid(update):
    with pytest.raises(ValidationError):
        spec(**update)


def test_end_to_end_and_replay(tmp_path):
    path = run(spec(), tmp_path)
    stored = load_run(path)
    assert stored["manifest"]["status"] == "COMPLETE"
    assert stored["manifest"]["authority"] == "NONE"
    assert len(stored["baseline"]) == 3
    assert len(stored["candidates"]) == 6
    assert all(c["trust"] == "UNVERIFIED" for c in stored["candidates"])
    assert stored["claims"] and stored["verification"]
    assert (
        stored["metrics"]["experimental"]["lexical_diversity"]
        > stored["metrics"]["baseline"]["lexical_diversity"]
    )
    assert "heuristic" in (path / "report.md").read_text()
    again = replay(path, tmp_path)
    second = load_run(again)
    assert path != again
    assert second["manifest"]["parent_run"] == path.name
    assert [c["text"] for c in stored["candidates"]] == [c["text"] for c in second["candidates"]]
    assert second["metrics"] == stored["metrics"]


def test_dream_then_wake_does_not_promote_generated_authority(tmp_path):
    path = run(spec(), tmp_path, wake_now=False)
    assert load_run(path)["manifest"]["status"] == "GENERATED"
    awake = wake(path, tmp_path)
    assert awake != path
    assert load_run(path)["manifest"]["status"] == "GENERATED"
    assert load_run(awake)["manifest"]["authority"] == "NONE"


def test_tamper_is_detected(tmp_path):
    path = run(spec(), tmp_path)
    with (path / "candidates.jsonl").open("a") as stream:
        stream.write("{}\n")
    with pytest.raises(ValueError, match="integrity"):
        load_run(path)


def test_privacy_and_replay_disabled(tmp_path):
    path = run(spec(retain_text=False), tmp_path)
    assert "Detect hallucination" not in (path / "experiment.json").read_text()
    assert "IDEA:" not in (path / "candidates.jsonl").read_text()
    with pytest.raises(ValueError, match="retention"):
        replay(path, tmp_path)


@pytest.mark.parametrize(
    "secret",
    [
        "sk-" + "a" * 25,
        "ghp_" + "b" * 36,
        "Authorization: Bearer abcdef",
        "password=hunter_fixture",
    ],
)
def test_redaction(secret):
    assert secret not in redact(secret)


def test_quoted_and_structured_secrets():
    assert "fixture-secret" not in redact('"api_key": "fixture-secret"')
    assert "fixture-secret" not in json.dumps(scrub({"Authorization": "Bearer fixture-secret"}))


def test_arithmetic_does_not_round_into_support():
    claims = extract(
        "CALC: 999999999999.99999999 * 999999999999.99999999 = 999999999999999999980000.0000", "c"
    )
    assert verify(claims, [])[0]["status"] == "CONTRADICTED"


def test_unresolved_claims_are_visible_in_metrics(tmp_path):
    artifacts = load_run(run(spec(), tmp_path))
    assert artifacts["metrics"]["experimental"]["unresolved_claims"] > 0


def test_missing_hash_entry_is_rejected(tmp_path):
    path = run(spec(), tmp_path)
    manifest = json.loads((path / "manifest.json").read_text())
    del manifest["file_hashes"]["candidates.jsonl"]
    (path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="integrity"):
        load_run(path)


def test_wake_rejects_authority_in_manifest(tmp_path):
    path = run(spec(), tmp_path)
    manifest = json.loads((path / "manifest.json").read_text())
    manifest["authority"] = "APPROVED"
    (path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="authority"):
        wake(path, tmp_path)


def test_wake_records_current_analysis_provenance(tmp_path):
    path = run(spec(), tmp_path)
    awake = load_run(wake(path, tmp_path))
    assert awake["manifest"]["analysis"]["implementation_hash"]
    assert awake["manifest"]["analysis"]["version"] == __version__


def test_baseline_redaction_disables_replay(tmp_path, monkeypatch):
    from howldream.providers import Response

    class Provider:
        capabilities = MockProvider().capabilities

        def generate(self, prompt, condition, index, temperature, seed):
            return Response(
                'password="fixture-secret"' if condition == "baseline" else "IDEA: testing",
                "fixture",
            )

    monkeypatch.setattr("howldream.engine.make_provider", lambda config: Provider())
    artifacts = load_run(run(spec(), tmp_path))
    assert not artifacts["manifest"]["replay_available"]


def test_replay_remote_needs_explicit_opt_in(tmp_path, monkeypatch):
    from howldream.artifacts import save_run

    path = run(spec(), tmp_path)
    artifacts = load_run(path)
    artifacts["experiment"]["provider"] = {
        "kind": "openai_compatible",
        "model": "configured",
        "allow_remote": True,
        "base_url": "https://example.com/v1",
    }
    save_run(path, artifacts)
    monkeypatch.setenv("HOWLDREAM_API_KEY", "fixture-secret")
    with pytest.raises(ValueError, match="remote replay"):
        replay(path, tmp_path)


def test_known_fact_and_uncertainty():
    experiment = spec()
    claims = extract("FACT: sky=blue\nFACT: sky=green\nFACT: moon=cheese\nUNKNOWN: moon", "c")
    results = verify(claims, experiment.evidence)
    assert [r["status"] for r in results] == [
        "ECHO",
        "CONTRADICTED",
        "UNSUPPORTED",
        "UNCERTAIN",
    ]
    assert results[0]["source_ids"] == ["s1"]
    assert all(c["status"] == "UNVERIFIED" for c in claims)


def test_mock_and_capabilities():
    provider = MockProvider()
    assert not provider.capabilities["supports_seed"]
    assert not provider.capabilities["supports_logprobs"]
    first = provider.generate("prompt", "baseline", 0, 0.2, 42)
    assert first.text == provider.generate("prompt", "baseline", 0, 0.2, 42).text
    assert first.usage is None


def test_remote_requires_explicit_egress():
    with pytest.raises(ValueError, match="allow_remote"):
        make_provider(spec(provider={"kind": "openai_compatible", "model": "configured"}).provider)


def test_missing_credentials(monkeypatch):
    monkeypatch.delenv("HOWLDREAM_API_KEY", raising=False)
    with pytest.raises(ValueError, match="HOWLDREAM_API_KEY"):
        make_provider(
            spec(
                provider={
                    "kind": "openai_compatible",
                    "model": "configured",
                    "allow_remote": True,
                    "base_url": "https://example.com/v1",
                }
            ).provider
        )


def test_duplicates_do_not_become_discoveries():
    candidates = [
        {"id": "a", "text": "IDEA: compare source order"},
        {"id": "b", "text": "IDEA: compare source order"},
    ]
    result = score_group(candidates, [])
    assert result[1]["duplicate_of"] == "a"
    assert result[1]["decision"] == "REJECT"


def test_common_words_do_not_make_noise_relevant():
    result = score_group(
        [{"id": "noise", "text": "IDEA: Build an unrelated purple carousel for entertainment."}],
        [],
        objective="Generate unconventional methods for detecting hallucination "
        "that do not depend exclusively on asking one LLM to judge another LLM.",
    )
    assert result[0]["decision"] == "REJECT"


def test_benchmark_is_larger_and_reports_observed_errors():
    result = benchmark()
    assert len(load_dataset()[0].cases) >= 100
    assert result["binary_confusion_matrix"]["true_positives"] > 0
    assert result["binary_confusion_matrix"]["true_negatives"] > 0
    assert result["claim_metrics"]["missed_claims"] > 0


def test_cli_happy_path(tmp_path):
    experiment = tmp_path / "experiment.json"
    experiment.write_text(spec().model_dump_json())
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "howldream.cli",
            "run",
            str(experiment),
            "--output",
            str(tmp_path / "runs"),
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "runs" / json.loads(result.stdout)["run_id"] / "report.md").exists()
