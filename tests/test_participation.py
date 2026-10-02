"""Participation provenance: Dream is credited only with what it actually did."""

import json
import subprocess
import sys

import pytest

from howldream.artifacts import load_run
from howldream.contracts import CandidateHandoff, ExplorationRequest
from howldream.engine import explore, installed_commit
from howldream.interop import export_candidate
from howldream.participation import cluster_external, export_external, record
from howldream.providers import CAPABILITIES, Response

IDEAS = {
    "objective": "Improve a small fictional engineering portfolio",
    "origin": {"component": "supervising-agent", "provider": "anthropic", "model": "claude-x"},
    "ideas": [
        {"id": "a", "text": "Lead with the release CLI and its verification numbers"},
        {"id": "b", "text": "Lead with the release CLI and verification numbers in context"},
        {"id": "c", "text": "Separate independent projects from professional work"},
    ],
}


class Fixture:
    capabilities = CAPABILITIES

    def generate(self, prompt, condition, index, temperature, seed):
        return Response(
            f"IDEA: portfolio option {index}",
            "authored-fixture",
            execution={"mocked": True, "inference_occurred": False},
        )


class Live(Fixture):
    def generate(self, prompt, condition, index, temperature, seed):
        return Response(
            f"IDEA: portfolio direction {['cli', 'tooling', 'labels'][index % 3]}",
            "claude-live",
            execution={"actual_provider": "claude", "mocked": False, "inference_occurred": True},
        )


def operations(records):
    return [r["operation"] for r in records]


def test_external_ideas_are_clustered_never_generated():
    discovery = cluster_external(IDEAS, ("objective_fit",))
    assert discovery["generated_by_howldream"] == 0
    assert operations(discovery["participation"]) == ["CLUSTERED", "RANKED"]
    clustered = discovery["participation"][0]
    assert clustered["origin_component"] == "supervising-agent"
    assert clustered["origin_model"] == "claude-x"
    assert clustered["transforming_component"] == "howldream"
    assert clustered["subject_count"] == 3
    assert "GENERATED" not in json.dumps(discovery)
    assert discovery["cluster_count"] == 2
    assert all(u["origin"]["component"] == "supervising-agent" for u in discovery["units"])


@pytest.mark.parametrize("origin", [None, {"component": "howldream"}, {"component": " "}])
def test_external_ideas_must_name_a_non_dream_origin(origin):
    with pytest.raises(ValueError):
        cluster_external({**IDEAS, "origin": origin})


def test_external_selection_exports_valid_candidate_with_full_participation():
    discovery = cluster_external(IDEAS)
    candidate = export_external(discovery, discovery["units"][2]["id"])
    CandidateHandoff.model_validate(candidate)
    participation = candidate["provenance"]["participation"]
    assert operations(participation) == ["CLUSTERED", "SELECTED"]
    assert candidate["provenance"]["origin"]["component"] == "supervising-agent"
    assert candidate["provenance"]["selection"]["operation"] == "SELECTED"


def test_fixture_run_is_not_credited_as_generated(tmp_path):
    path, result = explore(
        ExplorationRequest(request_id="r", objective="portfolio"), tmp_path, Fixture()
    )
    participation = load_run(path)["discovery"]["participation"]
    assert "GENERATED" not in operations(participation)
    assert participation[0]["operation"] == "NO_EFFECT"
    assert (
        result.candidates[0].provenance.model_extra["participation"][0]["operation"] == "NO_EFFECT"
    )


def test_live_run_records_generation_with_origin_model(tmp_path):
    path, result = explore(
        ExplorationRequest(request_id="r", objective="portfolio"), tmp_path, Live()
    )
    artifacts = load_run(path)
    participation = artifacts["discovery"]["participation"]
    assert operations(participation)[:2] == ["GENERATED", "CLUSTERED"]
    assert participation[0]["origin_model"] == "claude-live"
    assert participation[0]["origin_provider"] == "claude"
    assert artifacts["manifest"]["observed_models"] == ["claude-live"]
    candidate = result.candidates[0].provenance.model_extra["participation"][0]
    assert (candidate["operation"], candidate["origin_model"]) == ("GENERATED", "claude-live")


def test_unit_export_carries_generation_clustering_and_selection(tmp_path):
    path, _ = explore(ExplorationRequest(request_id="r", objective="portfolio"), tmp_path, Live())
    unit_id = load_run(path)["discovery"]["units"][0]["id"]
    unit = export_candidate(path, unit_id).model_dump()
    assert operations(unit["provenance"]["participation"]) == ["GENERATED", "CLUSTERED", "SELECTED"]
    assert unit["provenance"]["selection"]["selected_by"] == "operator"


def test_unknown_operation_rejected():
    with pytest.raises(ValueError):
        record("INVENTED", subject_count=1, origin_component="x")


def test_cluster_and_export_cli(tmp_path):
    ideas, out = tmp_path / "ideas.json", tmp_path / "discovery.json"
    ideas.write_text(json.dumps(IDEAS))
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "howldream.cli",
            "cluster",
            "--external",
            str(ideas),
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    unit_id = json.loads(out.read_text())["units"][0]["id"]
    exported = subprocess.run(
        [sys.executable, "-m", "howldream.cli", "export", str(out), "--candidate-id", unit_id],
        capture_output=True,
        text=True,
        check=False,
    )
    assert exported.returncode == 0, exported.stderr
    assert json.loads(exported.stdout)["provenance"]["participation"][-1]["operation"] == "SELECTED"


def test_installed_commit_is_none_or_hex():
    commit = installed_commit()
    assert commit is None or len(commit) == 40
