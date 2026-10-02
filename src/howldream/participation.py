"""Truthful participation records: what HowlDream actually did to an idea.

A Dream artifact can hold ideas Dream's provider generated, ideas a fixture
replayed, or ideas another model wrote and handed in for clustering. Those
are different contributions, and crediting Dream with "generated 20 ideas"
when it only clustered them is the attribution error Run 5 exposed.

Every record names the origin of the subject (component, provider, model)
separately from the component that operated on it and the operation
performed. Operations: GENERATED, CLUSTERED, RANKED, REVIEWED, VALIDATED,
TRANSFORMED, SELECTED, NO_EFFECT.
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from howldream.discovery import analyze_discovery

OPERATIONS = frozenset(
    {
        "GENERATED",
        "CLUSTERED",
        "RANKED",
        "REVIEWED",
        "VALIDATED",
        "TRANSFORMED",
        "SELECTED",
        "NO_EFFECT",
    }
)
EXTERNAL_SCHEMA = "howldream.external_discovery/v1"
MAX_EXTERNAL_IDEAS = 200
MAX_IDEA_CHARS = 2000


def record(
    operation: str,
    *,
    subject_count: int,
    origin_component: str,
    origin_provider: str | None = None,
    origin_model: str | None = None,
    transforming_component: str = "howldream",
    inference_occurred: bool = False,
    note: str = "",
) -> dict[str, Any]:
    if operation not in OPERATIONS:
        raise ValueError(f"unknown participation operation {operation!r}")
    return {
        "operation": operation,
        "transforming_component": transforming_component,
        "origin_component": origin_component,
        "origin_provider": origin_provider,
        "origin_model": origin_model,
        "subject_count": subject_count,
        "inference_occurred": inference_occurred,
        "note": note,
    }


def run_participation(candidates: list[dict], discovery: dict) -> list[dict]:
    """Participation for a normal Dream run, derived from each candidate's execution."""
    live = [
        c
        for c in candidates
        if (c.get("execution") or {}).get("inference_occurred") is True
        and not (c.get("execution") or {}).get("mocked")
    ]
    replayed = [c for c in candidates if c not in live]
    records = []
    if live:
        execution = live[0].get("execution") or {}
        models = sorted({str(c.get("model")) for c in live if c.get("model")})
        records.append(
            record(
                "GENERATED",
                subject_count=len(live),
                origin_component="howldream",
                origin_provider=execution.get("actual_provider"),
                origin_model=", ".join(models) or None,
                inference_occurred=True,
                note="Dream prompted the provider; the provider authored the text.",
            )
        )
    if replayed:
        records.append(
            record(
                "NO_EFFECT",
                subject_count=len(replayed),
                origin_component="fixture",
                origin_provider=(replayed[0].get("execution") or {}).get("actual_provider"),
                note="Fixture or mock output replayed; Dream did not generate it.",
            )
        )
    if discovery.get("idea_count"):
        records.append(
            record(
                "CLUSTERED",
                subject_count=discovery["idea_count"],
                origin_component="howldream"
                if live and not replayed
                else "mixed"
                if live
                else "fixture",
                note="Deterministic concept-token clustering; no inference.",
            )
        )
    if discovery.get("ranking"):
        records.append(
            record(
                "RANKED",
                subject_count=len(discovery["ranking"]),
                origin_component="howldream"
                if live and not replayed
                else "mixed"
                if live
                else "fixture",
                note="Advisory heuristic ranking; no execution authority.",
            )
        )
    return records


def _origin(value: Any) -> dict:
    raw = value.get("component") if isinstance(value, dict) else None
    component = raw.strip() if isinstance(raw, str) else ""
    if not component:
        raise ValueError("external ideas require origin.component naming who authored them")
    if component.lower() == "howldream":
        raise ValueError("externally supplied ideas cannot claim howldream as their origin")
    return {
        "component": component[:200],
        "provider": value.get("provider") if isinstance(value.get("provider"), str) else None,
        "model": value.get("model") if isinstance(value.get("model"), str) else None,
    }


def cluster_external(payload: dict, ranking_criteria: tuple[str, ...] = ()) -> dict:
    """Cluster ideas someone else wrote. Dream records CLUSTERED, never GENERATED.

    ``payload``: {"objective": str, "origin": {"component", "provider", "model"},
    "ideas": [{"id"?: str, "text": str}, ...]}.
    """
    if not isinstance(payload, dict):
        raise TypeError("external ideas payload must be a JSON object")
    origin = _origin(payload.get("origin"))
    objective = payload.get("objective")
    if not isinstance(objective, str) or not objective.strip():
        raise ValueError("external ideas payload requires an objective")
    ideas = payload.get("ideas")
    if not isinstance(ideas, list) or not ideas or len(ideas) > MAX_EXTERNAL_IDEAS:
        raise ValueError(f"ideas must be a list of 1 to {MAX_EXTERNAL_IDEAS} entries")
    candidates = []
    for index, idea in enumerate(ideas, start=1):
        text = idea.get("text") if isinstance(idea, dict) else idea
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_IDEA_CHARS:
            raise ValueError(f"ideas[{index - 1}] needs text of 1 to {MAX_IDEA_CHARS} characters")
        supplied = idea.get("id") if isinstance(idea, dict) else None
        candidates.append(
            {
                "id": f"ext-{index}",
                "supplied_id": supplied if isinstance(supplied, str) else None,
                "text": "IDEA: " + " ".join(text.split()),
            }
        )
    discovery = analyze_discovery(candidates, [], objective, [], [], ranking_criteria)
    by_candidate = {c["id"]: c for c in candidates}
    for unit in discovery["units"]:
        unit["origin"] = origin
        unit["supplied_id"] = by_candidate[unit["candidate_id"]]["supplied_id"]
    participation = [
        record(
            "CLUSTERED",
            subject_count=discovery["idea_count"],
            origin_component=origin["component"],
            origin_provider=origin["provider"],
            origin_model=origin["model"],
            note="Externally supplied ideas; Dream clustered them and generated none.",
        )
    ]
    if discovery["ranking"]:
        participation.append(
            record(
                "RANKED",
                subject_count=len(discovery["ranking"]),
                origin_component=origin["component"],
                origin_provider=origin["provider"],
                origin_model=origin["model"],
            )
        )
    payload_hash = sha256(
        repr(sorted((c["id"], c["text"]) for c in candidates)).encode()
    ).hexdigest()
    return {
        "schema": EXTERNAL_SCHEMA,
        "discovery_id": f"hdx-{payload_hash[:12]}",
        "created_at": datetime.now(UTC).isoformat(),
        "objective": objective,
        "origin": origin,
        "authority": "NONE",
        "participation": participation,
        "generated_by_howldream": 0,
        **discovery,
    }


def export_external(discovery: dict, unit_id: str) -> dict:
    """A howl.candidate/v1 for one externally authored idea Dream clustered and selected."""
    from howldream.contracts import CandidateHandoff

    if discovery.get("schema") != EXTERNAL_SCHEMA:
        raise ValueError("not a howldream external discovery artifact")
    unit = next((u for u in discovery["units"] if u["id"] == unit_id), None)
    if unit is None:
        raise ValueError("idea unit not present in external discovery")
    origin = discovery["origin"]
    participation = list(discovery["participation"]) + [
        record(
            "SELECTED",
            subject_count=1,
            origin_component=origin["component"],
            origin_provider=origin["provider"],
            origin_model=origin["model"],
            note="Operator selected this unit through `howldream export`.",
        )
    ]
    return CandidateHandoff.model_validate(
        {
            "candidate_id": f"{discovery['discovery_id']}/{unit['id']}",
            "source_run_id": discovery["discovery_id"],
            "parent_request_id": discovery["discovery_id"],
            "objective": discovery["objective"],
            "text": unit["text"],
            "provenance": {
                "producer_component": "howldream",
                "observation_kind": "EXTERNALLY_OBSERVED",
                "transformations": ["external_cluster", "idea_unit_selection"],
                "source_unit": {
                    k: unit[k] for k in ("id", "source_span", "source_hash", "cluster")
                },
                "origin": origin,
                "participation": participation,
                "selection": {
                    "selected_by": "operator",
                    "operation": "SELECTED",
                    "via": "howldream export",
                },
            },
        }
    ).model_dump()
