"""Identify only explicit canonical schemas or a strict evidence ledger."""

from pathlib import Path

import yaml
from pydantic import BaseModel

from howldream.contracts import (
    CandidateAssessment,
    CandidateHandoff,
    DevelopmentResult,
    ExplorationRequest,
    ExplorationResult,
)
from howldream.schema import Evidence, read_experiment


def validate_artifact(path: Path) -> dict:
    if path.stat().st_size > 2_000_000:
        raise ValueError("artifact exceeds 2 MB")
    value = yaml.safe_load(path.read_text())
    if isinstance(value, list) and value:
        evidence = [Evidence.model_validate(row) for row in value]
        if len({row.id for row in evidence}) != len(evidence):
            raise ValueError("duplicate evidence IDs")
        return {"valid": True, "artifact_type": "evidence_ledger"}
    if not isinstance(value, dict):
        raise TypeError("UNKNOWN_ARTIFACT_TYPE: expected versioned envelope or evidence list")
    version = value.get("schema_version")
    models: dict[str, type[BaseModel]] = {
        "howl.candidate/v1": CandidateHandoff,
        "howl.assessment/v1": CandidateAssessment,
        "howl.exploration/v1": ExplorationRequest,
        "howl.exploration_result/v1": ExplorationResult,
        "howl.development_result/v1": DevelopmentResult,
    }
    if type(version) is int and version == 1:
        experiment = read_experiment(path)
        return {"valid": True, "artifact_type": "experiment", "name": experiment.name}
    if isinstance(version, str) and version in models:
        models[version].model_validate(value)
        return {"valid": True, "artifact_type": version}
    raise ValueError(
        "UNKNOWN_ARTIFACT_TYPE: supported experiment (schema_version=1), "
        "howl.candidate/v1, howl.exploration/v1, howl.exploration_result/v1, "
        "howl.assessment/v1, howl.development_result/v1, or evidence list"
    )
