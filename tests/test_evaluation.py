"""Milestone Two benchmark and value-evaluation contracts."""

import json
import subprocess
import sys

import pytest
from pydantic import ValidationError

from howldream.benchmark import BenchmarkDataset, benchmark, confusion, load_dataset
from howldream.dreamvalue import ValueCandidate, condition_metrics, evaluate, load_suite


def test_dreambench_schema_version_splits_and_provenance():
    dataset, digest = load_dataset()
    assert dataset.version == "0.2.0"
    assert len(dataset.cases) == 156
    assert len(digest) == 64
    splits = {
        name: {case.id for case in dataset.cases if case.split == name}
        for name in (
            "development",
            "validation",
            "held_out",
            "confirmation",
        )
    }
    assert all(splits.values())
    assert not (splits["development"] & splits["validation"])
    assert not (splits["development"] & splits["held_out"])
    assert not (splits["validation"] & splits["held_out"])
    assert not (splits["held_out"] & splits["confirmation"])
    assert all(case.source and case.expected_behavior for case in dataset.cases)


def test_dreambench_rejects_unknown_version_and_missing_labels():
    dataset, _ = load_dataset()
    raw = dataset.model_dump(mode="json")
    raw["schema_version"] = 2
    with pytest.raises(ValidationError):
        BenchmarkDataset.model_validate(raw)
    raw = dataset.model_dump(mode="json")
    del raw["cases"][0]["expected_classification"]
    with pytest.raises(ValidationError):
        BenchmarkDataset.model_validate(raw)


def test_split_runner_and_claim_metrics(tmp_path):
    development = benchmark("development", tmp_path)
    held_out = benchmark("held_out", tmp_path)
    assert development["cases"] == 65
    assert held_out["cases"] == 39
    assert development["held_out_execution"] is False
    assert held_out["held_out_execution"] is True
    assert development["claim_metrics"]["missed_claims"] > 0
    assert development["binary_confusion_matrix"]["false_negatives"] > 0
    artifact = tmp_path / "dreambench_0.2.0_held_out.json"
    assert json.loads(artifact.read_text())["dataset_hash"] == held_out["dataset_hash"]
    assert (tmp_path / "dreambench_0.2.0_held_out.md").exists()
    assert development["implementation_hash"]
    assert set(development["category_confusion"]) >= {"FABRICATION", "NUMERIC_ERROR"}


def test_verification_does_not_use_annotation_oracle(tmp_path):
    dataset, _ = load_dataset()
    baseline = benchmark("development")["binary_confusion_matrix"]
    raw = dataset.model_dump(mode="json")
    for case in raw["cases"]:
        for claim in case["claims"]:
            claim["verification_input"] = "FACT: annotation_oracle=must_not_be_used"
    altered = tmp_path / "altered.json"
    altered.write_text(json.dumps(raw))
    assert benchmark("development", dataset=altered)["binary_confusion_matrix"] == baseline


def test_confusion_handles_zero_denominators():
    result = confusion([{"expected_problematic": False, "predicted_problematic": False}])
    assert result["precision"] is None
    assert result["recall"] is None
    assert result["specificity"] == 1.0
    assert result["f1"] is None


def test_dreamvalue_fairness_metrics_and_curves(tmp_path):
    suite, digest = load_suite()
    assert len(suite.tasks) == 24
    assert len(digest) == 64
    result = evaluate(review_output=tmp_path)
    assert result["baseline"]["candidates"] == result["dream"]["candidates"] == 240
    assert (
        result["dream"]["unique_conceptual_clusters"]
        > result["baseline"]["unique_conceptual_clusters"]
    )
    assert result["dream"]["unsupported_claim_rate"] > result["baseline"]["unsupported_claim_rate"]
    assert len(result["divergence_curve"]) >= 4
    assert [row["candidates_per_task"] for row in result["candidate_count_curve"]] == [
        3,
        5,
        10,
    ]
    packet = json.loads((tmp_path / "dreamvalue_blind_review.json").read_text())
    assert packet["blinded"] and packet["supports_independent_reviewers"]
    assert all(
        "condition" not in candidate for task in packet["tasks"] for candidate in task["candidates"]
    )


def test_conceptual_duplicate_and_empty_metrics():
    candidate = ValueCandidate(
        id="one",
        condition="dream",
        approach="same",
        text="one",
        relevance=True,
        unsupported=False,
        outcome="INVESTIGATE",
        divergence=0.5,
        ordinal=1,
    )
    result = condition_metrics([candidate, candidate.model_copy(update={"id": "two"})])
    assert result["duplicate_rate"] == 0.5
    assert result["verified_novel_candidate_yield"] == 0.0
    assert condition_metrics([])["verified_novel_candidate_yield"] is None


@pytest.mark.parametrize(
    "arguments",
    [
        ["benchmark", "list"],
        ["benchmark", "run", "dreambench", "--split", "development"],
        ["evaluate", "dreamvalue"],
    ],
)
def test_evaluation_cli(arguments, tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "howldream.cli",
            *arguments,
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)
