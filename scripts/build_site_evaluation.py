"""Derive public evaluation data from canonical checked-in artifacts."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "evaluation" / "results"


def pick(metrics: dict) -> dict:
    keys = (
        "candidates",
        "lexical_diversity",
        "unique_conceptual_clusters",
        "duplicate_rate",
        "unsupported_claim_rate",
        "investigate_rate",
        "survives_verification_rate",
        "verified_novel_candidate_yield",
    )
    return {key: metrics[key] for key in keys}


def main() -> None:
    held_out = json.loads((RESULTS / "dreambench_0.2.0_held_out.json").read_text())
    confirmation = json.loads((RESULTS / "dreambench_0.2.0_confirmation.json").read_text())
    value = json.loads((RESULTS / "dreamvalue_results.json").read_text())
    payload = {
        "schema": "howldream.site_evaluation/v1",
        "source_artifacts": [
            "../evaluation/results/dreambench_0.2.0_held_out.json",
            "../evaluation/results/dreambench_0.2.0_confirmation.json",
            "../evaluation/results/dreamvalue_results.json",
        ],
        "dreambench": {
            "version": held_out["benchmark_version"],
            "held_out_cases": held_out["cases"],
            "held_out_claims": held_out["claim_metrics"],
            "held_out_confusion": held_out["binary_confusion_matrix"],
            "confirmation_cases": confirmation["cases"],
            "confirmation_confusion": confirmation["binary_confusion_matrix"],
            "category_recall": held_out["category_classification"]["recall"],
        },
        "dreamvalue": {
            "version": value["version"],
            "tasks": value["tasks"],
            "baseline": pick(value["baseline"]),
            "dream": pick(value["dream"]),
            "status": "authored evaluator calibration; independent human labels pending",
        },
        "promotion_decision": "HOLD",
    }
    (ROOT / "docs" / "evaluation.json").write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
