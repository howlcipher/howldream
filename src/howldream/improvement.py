"""Bounded deterministic improvement hypotheses, without provider calls."""

from importlib import import_module
from pathlib import Path
from typing import Any


def advise(path: Path) -> dict[str, Any]:
    try:
        cli = import_module("howlloop.cli")
        analysis = import_module("howlloop.analysis")
    except ImportError as exc:
        raise ValueError("Install HowlLoop in the HowlDream environment") from exc
    candidate = analysis.validate_candidate(cli.read_json(path))
    problem = candidate["problem"]
    if problem == "latency":
        hypothesis = "A repeated stage may be waiting or doing unnecessary work."
        experiment = "Profile the stage and alternate matched baseline and candidate samples."
        benefit = "Lower latency while preserving output and resource limits."
        disadvantage = "Removing waits can make output incomplete or unstable."
    elif problem == "friction":
        hypothesis = "A workflow default or diagnostic may be causing repeated rework."
        experiment = "Reproduce the reported correction and compare the required operator steps."
        benefit = "Fewer manual corrections for the same quality bar."
        disadvantage = "A changed default may disrupt other legitimate workflows."
    else:
        hypothesis = "A stage may have a reproducible input or environment dependency."
        experiment = "Reproduce the outcome and isolate a failing stage with a safe fixture."
        benefit = "Fewer unsuccessful operations while preserving useful existing behavior."
        disadvantage = "A narrow fix could mask other failures or weaken a fidelity check."
    return {
        "schema": "howldream.improvement_advice/v1",
        "candidate_id": candidate["candidate_id"],
        "authority": "none",
        "source": "hypothesis",
        "provider_calls": 0,
        "evidence": candidate["evidence"],
        "problem": f"{candidate['project']} {candidate['operation']}: {problem}",
        "hypothesis": hypothesis,
        "expected_benefit": benefit,
        "potential_disadvantage": disadvantage,
        "experiment": experiment,
        "required_checks": [
            "reproduce_baseline",
            "validate_candidate_output",
            "run_existing_regression_checks",
            "compare_controlled_samples",
        ],
        "estimated_scope": "one stage until the cause is reproduced",
        "uncertainty": "Recurring observations do not establish a root cause or benefit.",
    }
