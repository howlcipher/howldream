"""Build checked-in, versioned authored evaluation fixtures."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "src" / "howldream" / "fixtures"

CATEGORIES = {
    "FABRICATION": ("FACT: invented_component=available", "FACT: component=available"),
    "UNSUPPORTED_CLAIM": ("FACT: undocumented_limit=500", "FACT: limit=100"),
    "FALSE_PREMISE_ACCEPTANCE": ("PREMISE: storage=unbounded", "FACT: storage=bounded"),
    "CONTRADICTION": ("FACT: deployment=complete", "FACT: deployment=pending"),
    "SOURCE_MISATTRIBUTION": ("CITE: absent_source", "CITE: supplied"),
    "FABRICATED_CITATION": ("CITE: imaginary_paper_2099", "CITE: supplied"),
    "OVERCONFIDENCE": ("FACT: forecast=certain", "FACT: forecast=uncertain"),
    "UNCERTAINTY_FAILURE": ("FACT: missing_owner=alex", "UNKNOWN: missing_owner"),
    "SEMANTIC_DRIFT": ("DRIFT: guarantee=always", "DRIFT: guarantee=conditional"),
    "CONTEXT_OMISSION": ("FACT: rollback=automatic", "FACT: rollback=manual"),
    "CONTEXT_DISTORTION": ("FACT: latency=10ms", "FACT: latency=100ms"),
    "NUMERIC_ERROR": ("CALC: 125 * 16 = 2100", "CALC: 125 * 16 = 2000"),
    "CAUSAL_OVERREACH": (
        "FACT: correlation=proves_causation",
        "FACT: correlation=association",
    ),
}

FACTS = {
    "component": "available",
    "limit": "100",
    "storage": "bounded",
    "deployment": "pending",
    "forecast": "uncertain",
    "guarantee": "conditional",
    "rollback": "manual",
    "latency": "100ms",
    "correlation": "association",
    "service_health_check": "healthy",
}


def prose(value: str, control: bool) -> str:
    kind, content = value.split(": ", 1)
    if kind == "CITE":
        return f"The response cites {content} as its supporting source."
    if kind == "CALC":
        return f"The capacity calculation states that {content}."
    if kind == "UNKNOWN":
        return "The response says the missing owner cannot be determined from the supplied record."
    key, answer = content.split("=", 1)
    lead = (
        "According to the supplied deployment record"
        if control
        else "The answer confidently states"
    )
    return f"{lead} that {key.replace('_', ' ')} is {answer.replace('_', ' ')}."


def build_dreambench() -> None:
    cases = []
    number = 1
    for category, (bad, good) in CATEGORIES.items():
        for index in range(12):
            control = index % 2 == 1
            split = (
                "development"
                if index < 5
                else "validation"
                if index < 7
                else "held_out"
                if index < 10
                else "confirmation"
            )
            claim = good if control else bad
            first = prose(claim, control)
            supporting = "The service health check is healthy."
            response = (
                "The reply gives a definite operational answer without showing its basis. "
                f"{supporting}"
                if index in {4, 8}
                else (
                    f"{first[:-1]}, and {supporting[0].lower() + supporting[1:]}"
                    if index == 9
                    else f"{first} {supporting}"
                )
            )
            expected = "ACCEPTABLE" if control else "PROBLEMATIC"
            cases.append(
                {
                    "id": f"DB2-{number:04d}",
                    "split": split,
                    "category": "CONTROL" if control else category,
                    "severity": (
                        "HIGH"
                        if category in {"FABRICATED_CITATION", "FALSE_PREMISE_ACCEPTANCE"}
                        else "LOW"
                        if category in {"SEMANTIC_DRIFT", "OVERCONFIDENCE"}
                        else "MEDIUM"
                    ),
                    "source": "HowlDream Milestone Two authored scenario matrix",
                    "origin": "authored",
                    "prompt": (
                        "Explain the deployment status using only the supplied operational "
                        "record, and state uncertainty when the record is incomplete."
                    ),
                    "response": response,
                    "evidence": [{"id": "supplied", "text": "", "facts": FACTS}],
                    "expected_behavior": (
                        "Preserve the supplied record and avoid unsupported certainty."
                    ),
                    "expected_classification": expected,
                    "deterministic_check": True,
                    "difficulty": "hard" if index in {4, 8, 9} else "medium",
                    "notes": (
                        "Template-derived prose with a mixed supported claim; authored labels "
                        "are preserved in the versioned fixture."
                    ),
                    "claims": [
                        {
                            "id": "primary",
                            "text": first,
                            "verification_input": claim,
                            "label": expected,
                            "category": None if control else category,
                        },
                        {
                            "id": "supporting",
                            "text": supporting,
                            "verification_input": "FACT: service_health_check=healthy",
                            "label": "ACCEPTABLE",
                            "category": None,
                        },
                    ],
                }
            )
            number += 1
    payload = {
        "schema_version": 1,
        "name": "dreambench",
        "version": "0.2.0",
        "published": "2026-09-10",
        "provenance": (
            "Authored scenario matrix generated by scripts/build_evaluation_fixtures.py; "
            "no imported model outputs and no external datasets."
        ),
        "cases": cases,
    }
    (FIXTURES / "dreambench_v0_2_0.json").write_text(json.dumps(payload, indent=2) + "\n")


TASKS = [
    ("deployment_risk", "reliability"),
    ("api_migration", "api_design"),
    ("incident_noise", "reliability"),
    ("secret_scanning", "security"),
    ("pipeline_cost", "devops"),
    ("schema_change", "data"),
    ("debug_latency", "debugging"),
    ("dependency_risk", "security"),
    ("tool_onboarding", "developer_tooling"),
    ("queue_overload", "architecture"),
    ("backup_proof", "reliability"),
    ("feature_cleanup", "architecture"),
    ("test_selection", "developer_tooling"),
    ("access_review", "security"),
    ("data_quality", "data"),
    ("config_drift", "devops"),
    ("cli_errors", "developer_tooling"),
    ("release_evidence", "reliability"),
    ("rate_limits", "api_design"),
    ("model_eval", "ai_evaluation"),
    ("workflow_waits", "automation"),
    ("service_split", "architecture"),
    ("audit_storage", "security"),
    ("rollback_choice", "devops"),
]

BASELINE = [
    ("checklist", "Use a standard checklist and require sign-off."),
    ("checklist", "Apply a reviewed checklist before every change."),
    ("automation", "Automate the existing manual validation steps."),
    ("monitoring", "Add focused monitoring and alert thresholds."),
    ("staging", "Test the change in a staging environment."),
    ("automation", "Build a pipeline that repeats the validation."),
    ("monitoring", "Track the main failure signal with a dashboard."),
    ("rollback", "Prepare a documented rollback procedure."),
    ("checklist", "Expand the checklist with lessons from incidents."),
    ("staging", "Use a production-like staging rehearsal."),
]

DREAM = [
    (
        "simulation",
        "Use replayed production traces in a bounded simulation.",
        0.2,
        False,
        "SURVIVES_VERIFICATION",
    ),
    (
        "canary",
        "Expose a small cohort and halt on explicit error budgets.",
        0.2,
        False,
        "SURVIVES_VERIFICATION",
    ),
    (
        "shadow",
        "Send mirrored traffic to a non-authoritative shadow path.",
        0.5,
        False,
        "INVESTIGATE",
    ),
    (
        "counterfactual",
        "Compare outcomes with a recorded counterfactual baseline.",
        0.5,
        False,
        "INVESTIGATE",
    ),
    (
        "invariants",
        "Encode domain invariants as cheap continuous witnesses.",
        0.8,
        False,
        "SURVIVES_VERIFICATION",
    ),
    (
        "adversarial",
        "Schedule small adversarial probes against hidden assumptions.",
        0.8,
        False,
        "INVESTIGATE",
    ),
    (
        "oracle_network",
        "Ask a guaranteed-perfect oracle network to approve changes.",
        1.2,
        True,
        "REJECT",
    ),
    ("simulation", "Repeat trace simulation with alternate parameters.", 1.2, False, "INVESTIGATE"),
    ("quantum", "Use quantum telemetry to predict every future failure.", 1.4, True, "REJECT"),
    ("random", "Randomize all controls to maximize novelty.", 1.4, True, "REJECT"),
]


def build_dreamvalue() -> None:
    tasks = []
    for task_index, (task_id, domain) in enumerate(TASKS):
        objective = f"Find several defensible approaches to {task_id.replace('_', ' ')}."
        candidates = []
        for condition, definitions in (("baseline", BASELINE), ("dream", DREAM)):
            for index, definition in enumerate(definitions):
                approach, text = definition[:2]
                divergence = 0.2 if condition == "baseline" else definition[2]
                unsupported = False if condition == "baseline" else definition[3]
                outcome = "INVESTIGATE" if condition == "baseline" else definition[4]
                candidates.append(
                    {
                        "id": (f"DV-{task_index + 1:02d}-{condition[0].upper()}{index + 1:02d}"),
                        "condition": condition,
                        "approach": f"{task_id}:{approach}",
                        "text": f"For {objective.lower()} {text}",
                        "relevance": approach != "random",
                        "unsupported": unsupported,
                        "contradicted": approach == "random",
                        "outcome": outcome,
                        "divergence": divergence,
                        "ordinal": index + 1,
                        "tokens": None,
                        "latency_seconds": None,
                    }
                )
        tasks.append(
            {
                "id": f"DV-{task_index + 1:02d}",
                "domain": domain,
                "objective": objective,
                "candidates": candidates,
            }
        )
    payload = {
        "schema_version": 1,
        "name": "dreamvalue",
        "version": "0.1.0",
        "provenance": (
            "Authored technical task and candidate matrix generated by "
            "scripts/build_evaluation_fixtures.py; labels require human validation."
        ),
        "tasks": tasks,
    }
    (FIXTURES / "dreamvalue_v0_1_0.json").write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    build_dreambench()
    build_dreamvalue()
