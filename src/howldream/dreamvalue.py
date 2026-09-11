"""Transparent evaluation of useful conceptual exploration."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from importlib.resources import files
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from howldream.scoring import distance


class ValueModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ValueCandidate(ValueModel):
    id: str
    condition: str
    approach: str
    text: str
    relevance: bool
    unsupported: bool
    contradicted: bool = False
    outcome: str
    divergence: float = Field(ge=0, le=2)
    ordinal: int = Field(ge=1)
    tokens: int | None = None
    latency_seconds: float | None = None


class ValueTask(ValueModel):
    id: str
    domain: str
    objective: str
    candidates: list[ValueCandidate]

    @model_validator(mode="after")
    def has_fair_conditions(self):
        conditions = {candidate.condition for candidate in self.candidates}
        if not {"baseline", "dream"} <= conditions:
            raise ValueError("each task requires baseline and dream candidates")
        counts = Counter(candidate.condition for candidate in self.candidates)
        if counts["baseline"] != counts["dream"]:
            raise ValueError("baseline and dream candidate counts must be equal")
        return self


class ValueSuite(ValueModel):
    schema_version: Literal[1]
    name: Literal["dreamvalue"]
    version: str
    provenance: str
    tasks: list[ValueTask]


def load_suite(path: Path | None = None) -> tuple[ValueSuite, str]:
    target = path or Path(str(files("howldream").joinpath("fixtures/dreamvalue_v0_1_0.json")))
    raw = target.read_bytes()
    return ValueSuite.model_validate_json(raw), hashlib.sha256(raw).hexdigest()


def condition_metrics(candidates: list[ValueCandidate]) -> dict:
    pairs = [(a, b) for index, a in enumerate(candidates) for b in candidates[index + 1 :]]
    approaches = Counter(candidate.approach for candidate in candidates)
    duplicates = sum(count - 1 for count in approaches.values())
    investigate = sum(
        candidate.outcome in {"INVESTIGATE", "SURVIVES_VERIFICATION"} for candidate in candidates
    )
    survives = sum(candidate.outcome == "SURVIVES_VERIFICATION" for candidate in candidates)
    verified_novel = sum(
        candidate.relevance
        and not candidate.unsupported
        and not candidate.contradicted
        and candidate.outcome in {"INVESTIGATE", "SURVIVES_VERIFICATION"}
        and approaches[candidate.approach] == 1
        for candidate in candidates
    )
    count = len(candidates)
    return {
        "candidates": count,
        "lexical_diversity": (
            sum(distance(a.text, b.text) for a, b in pairs) / len(pairs) if pairs else 0.0
        ),
        "unique_conceptual_clusters": len(approaches),
        "conceptual_diversity": len(approaches) / count if count else None,
        "duplicate_rate": duplicates / count if count else None,
        "irrelevant_rate": sum(not candidate.relevance for candidate in candidates) / count
        if count
        else None,
        "unsupported_claim_rate": sum(candidate.unsupported for candidate in candidates) / count
        if count
        else None,
        "contradiction_rate": sum(candidate.contradicted for candidate in candidates) / count
        if count
        else None,
        "investigate_count": investigate,
        "investigate_rate": investigate / count if count else None,
        "survives_verification_count": survives,
        "survives_verification_rate": survives / count if count else None,
        "verified_novel_candidate_count": verified_novel,
        "verified_novel_candidate_yield": verified_novel / count if count else None,
        "tokens": sum(candidate.tokens or 0 for candidate in candidates) or None,
        "latency_seconds": sum(candidate.latency_seconds or 0 for candidate in candidates) or None,
        "cluster_distribution": dict(sorted(approaches.items())),
    }


def _curves(candidates: list[ValueCandidate]) -> tuple[list[dict], list[dict]]:
    divergence = []
    for level in sorted({candidate.divergence for candidate in candidates}):
        group = [candidate for candidate in candidates if candidate.divergence == level]
        divergence.append({"divergence": level, **condition_metrics(group)})
    count_curve = []
    for count in (3, 5, 10, 20, 40):
        group = [candidate for candidate in candidates if candidate.ordinal <= count]
        count_curve.append(
            {
                "candidates_per_task": min(count, max(c.ordinal for c in candidates)),
                **condition_metrics(group),
            }
        )
        if count >= max(candidate.ordinal for candidate in candidates):
            break
    return divergence, count_curve


def evaluate(suite_path: Path | None = None, review_output: Path | None = None) -> dict:
    suite, digest = load_suite(suite_path)
    grouped: dict[str, list[ValueCandidate]] = {
        condition: [] for condition in ("baseline", "dream")
    }
    for task in suite.tasks:
        for candidate in task.candidates:
            grouped[candidate.condition].append(candidate)
    baseline, dream = grouped["baseline"], grouped["dream"]
    divergence_curve, candidate_count_curve = _curves(dream)
    result = {
        "schema": "howldream.dreamvalue_run/v1",
        "suite": suite.name,
        "version": suite.version,
        "dataset_hash": digest,
        "tasks": len(suite.tasks),
        "methodology": {
            "conceptual_clusters": "authored approach labels; deterministic and human-defined",
            "outcomes": "authored review labels; human-judged, not model verification",
            "vncy": (
                "unique approach, relevant, not unsupported or contradicted, and "
                "INVESTIGATE or SURVIVES_VERIFICATION divided by all candidates"
            ),
            "fairness": "equal candidate counts per task and condition",
        },
        "baseline": condition_metrics(baseline),
        "dream": condition_metrics(dream),
        "divergence_curve": divergence_curve,
        "candidate_count_curve": candidate_count_curve,
        "limitations": [
            "Approach and outcome labels are authored judgments and require independent review.",
            "The deterministic suite tests evaluator behavior, not live-model causal effects.",
            "Task prompts and candidate pools are small and technical-domain weighted.",
        ],
    }
    if review_output:
        review_output.mkdir(parents=True, exist_ok=True)
        rng = random.Random(20260910)
        packet = []
        for task in suite.tasks:
            candidates = list(task.candidates)
            rng.shuffle(candidates)
            packet.append(
                {
                    "task_id": task.id,
                    "domain": task.domain,
                    "objective": task.objective,
                    "candidates": [
                        {
                            "review_id": f"{task.id}-R{index + 1:02d}",
                            "candidate": candidate.text,
                            "evidence": "See retained suite annotation after unblinding.",
                            "unsupported_assumptions": "",
                            "reviewer": "",
                            "useful": "",
                            "novel": "",
                            "feasible": "",
                            "worth_investigating": "",
                            "notes": "",
                        }
                        for index, candidate in enumerate(candidates)
                    ],
                }
            )
        packet_data = {
            "schema": "howldream.human_review/v1",
            "blinded": True,
            "supports_independent_reviewers": True,
            "tasks": packet,
        }
        (review_output / "dreamvalue_blind_review.json").write_text(
            json.dumps(packet_data, indent=2) + "\n"
        )
        (review_output / "dreamvalue_results.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
