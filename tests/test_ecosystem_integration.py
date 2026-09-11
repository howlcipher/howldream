"""Tests for HowlDream Milestone Four native ecosystem contracts and exploration."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from howldream.contracts import (
    DescentDAG,
    DescentNode,
    ExplorationRequest,
)
from howldream.engine import explore


def make_request(**overrides) -> ExplorationRequest:
    base = {
        "schema_version": "howl.exploration/v1",
        "request_id": "req-test-001",
        "objective": "Explore alternative diagnostic strategies for deployment timeouts",
        "originating_component": "howlplane",
        "requested_mode": "dream",
        "constraints": ["no_downtime", "local_diagnostics_only"],
        "evidence_refs": [
            {
                "id": "doc_1",
                "text": "Deployments fail intermittently at step 3.",
                "facts": {"timeout": "30s"},
            },
            {
                "id": "doc_2",
                "text": "Network saturation observed during peak hours.",
                "facts": {"latency": "high"},
            },
        ],
        "budget": {
            "max_candidates": 4,
            "max_trials": 1,
            "max_tokens": 256,
            "max_duration_seconds": 60,
            "provider_allowlist": ["mock"],
            "local_only": True,
        },
        "provenance": {"initiator": "test_suite", "commit": "abcdef1234"},
    }
    base.update(overrides)
    return ExplorationRequest.model_validate(base)


def test_exploration_request_validation():
    req = make_request()
    assert req.request_id == "req-test-001"
    assert req.authority.type == "ADVISORY"
    assert req.authority.executable is False


def test_fail_closed_on_authority_escalation():
    with pytest.raises(ValidationError):
        make_request(authority={"type": "EXECUTIVE", "executable": False})

    with pytest.raises(ValidationError):
        make_request(authority={"type": "ADVISORY", "executable": True})


def test_explore_end_to_end(tmp_path: Path):
    req = make_request()
    run_dir, result = explore(req, tmp_path)

    assert run_dir.exists()
    assert (run_dir / "exploration_envelope.json").exists()
    assert (run_dir / "manifest.json").exists()

    # Verify exploration result structure
    assert result.schema_version == "howl.exploration_result/v1"
    assert result.parent_request_id == req.request_id
    assert result.authority.type == "ADVISORY"
    assert result.authority.executable is False
    assert len(result.candidates) == 4

    for cand in result.candidates:
        assert cand.schema_version == "howl.candidate/v1"
        assert cand.trust == "UNVERIFIED"
        assert cand.authority.type == "ADVISORY"
        assert cand.authority.executable is False
        assert cand.parent_request_id == req.request_id

    # Verify descent DAG
    dag = result.descent_dag
    obj_id = f"obj-{req.request_id}"
    assert obj_id in dag.nodes
    assert f"{run_dir.name}/dream" in dag.nodes

    # Trace candidate back to objective
    cand0_id = result.candidates[0].candidate_id
    trace_nodes = dag.trace(cand0_id)
    node_types = [n.node_type for n in trace_nodes]
    assert "CANDIDATE" in node_types
    assert "DREAM_RUN" in node_types
    assert "OBJECTIVE" in node_types


def test_descent_dag_serialization():
    dag = DescentDAG()
    dag.add_node(DescentNode(node_id="root", node_type="OBJECTIVE", label="Root Objective"))
    dag.add_node(DescentNode(node_id="cand_1", node_type="CANDIDATE", label="Candidate 1"))
    dag.add_edge("root", "cand_1", "generates")

    trace = dag.trace("cand_1")
    assert len(trace) == 2
    assert trace[0].node_id == "cand_1"
    assert trace[1].node_id == "root"


def test_cli_explore_and_trace(tmp_path: Path):
    req_file = tmp_path / "request.json"
    req = make_request()
    req_file.write_text(req.model_dump_json(indent=2))

    runs_dir = tmp_path / "runs"

    # Run explore via CLI
    cmd_explore = [
        sys.executable,
        "-m",
        "howldream.cli",
        "explore",
        str(req_file),
        "--output",
        str(runs_dir),
    ]
    res_exp = subprocess.run(cmd_explore, capture_output=True, text=True, check=True)
    exp_data = json.loads(res_exp.stdout)
    assert exp_data["schema_version"] == "howl.exploration_result/v1"
    assert len(exp_data["candidates"]) == 4

    cand_id = exp_data["candidates"][0]["candidate_id"]

    # Run trace via CLI
    cmd_trace = [
        sys.executable,
        "-m",
        "howldream.cli",
        "trace",
        cand_id,
        "--output",
        str(runs_dir),
    ]
    res_trace = subprocess.run(cmd_trace, capture_output=True, text=True, check=True)
    trace_data = json.loads(res_trace.stdout)
    assert len(trace_data) >= 3
    assert any(n["node_type"] == "OBJECTIVE" for n in trace_data)
