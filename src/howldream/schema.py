"""Strict, bounded, versioned experiment input."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Generation(StrictModel):
    candidates: int = Field(default=6, ge=1, le=100)
    temperature: float = Field(default=1.2, ge=0, le=2)


class ProviderConfig(StrictModel):
    kind: Literal["mock", "ollama", "openai_compatible", "command"] = "mock"
    model: str = Field(default="fixture-v1", min_length=1, max_length=200)
    base_url: str | None = None
    allow_remote: bool = False
    allow_local_inference: bool = False
    forbid_local_inference: bool = False
    timeout_seconds: int = Field(default=120, ge=1, le=600)
    max_tokens: int = Field(default=512, ge=32, le=4096)


class Evidence(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_./-]{1,100}$")
    text: str = Field(default="", max_length=50000)
    facts: dict[str, str] = Field(default_factory=dict)


class Perturbation(StrictModel):
    kind: Literal["omit_context", "reverse_context", "false_premise", "contradict_context"]
    text: str = Field(default="", max_length=5000)


class Experiment(StrictModel):
    schema_version: Literal[1]
    name: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,100}$")
    objective: str = Field(min_length=1, max_length=10000)
    hypothesis: str = Field(default="", max_length=10000)
    mode: Literal["dream", "nightmare"] = "dream"
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    baseline: Generation = Field(default_factory=lambda: Generation(candidates=3, temperature=0.2))
    generation: Generation = Field(default_factory=Generation)
    max_calls: int = Field(default=500, ge=0, le=500)
    trials: int = Field(default=1, ge=1, le=20)
    seed: int = Field(default=42, ge=0, le=2**31 - 1)
    evidence: list[Evidence] = Field(default_factory=list, max_length=100)
    context: list[str] = Field(default_factory=list, max_length=20)
    speculative_candidates: list[dict] = Field(default_factory=list, max_length=50)
    perturbations: list[Perturbation] = Field(default_factory=list, max_length=10)
    retain_text: bool = True

    @field_validator("schema_version", mode="before")
    @classmethod
    def exact_version_type(cls, value):
        if type(value) is not int:
            raise ValueError("schema_version must be integer 1")
        return value

    @model_validator(mode="after")
    def unique_sources(self):
        ids = [source.id for source in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence IDs must be unique")
        if self.trials * (self.baseline.candidates + self.generation.candidates) > 500:
            raise ValueError("experiment budget exceeds 500 total generations")
        return self


def read_experiment(path: Path) -> Experiment:
    if path.stat().st_size > 1_000_000:
        raise ValueError("experiment exceeds 1 MB")
    value = Experiment.model_validate(yaml.safe_load(path.read_text()))
    sources = list(value.evidence)
    for index, relative in enumerate(value.context):
        context = (path.parent / relative).resolve()
        if context.stat().st_size > 50000:
            raise ValueError(f"context[{index}] exceeds 50 KB")
        sources.append(Evidence(id=f"context/{index}", text=context.read_text()))
    # Snapshot file contents; replay must not reread mutable original files.
    return Experiment.model_validate(
        {**value.model_dump(), "evidence": [s.model_dump() for s in sources], "context": []}
    )
