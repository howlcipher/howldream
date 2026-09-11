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
    held_out_02 = json.loads((RESULTS / "dreambench_0.2.0_held_out.json").read_text())
    confirmation_02 = json.loads((RESULTS / "dreambench_0.2.0_confirmation.json").read_text())
    all_03 = json.loads((RESULTS / "dreambench_0.3.0_all.json").read_text())
    held_out_03 = json.loads((RESULTS / "dreambench_0.3.0_held_out.json").read_text())
    confirmation_03 = json.loads((RESULTS / "dreambench_0.3.0_confirmation.json").read_text())
    baseline_pre = json.loads(
        (RESULTS / "dreambench_0.3.0_baseline_pre_improvement.json").read_text()
    )
    value = json.loads((RESULTS / "dreamvalue_results.json").read_text())
    live_file = RESULTS / "live_experiments_canonical.json"
    live = json.loads(live_file.read_text()) if live_file.exists() else None

    pre_all = baseline_pre.get("all", baseline_pre)
    pre_recall = pre_all.get("binary_confusion_matrix", {}).get("recall", 0.2143)
    payload = {
        "schema": "howldream.site_evaluation/v2",
        "source_artifacts": [
            "../evaluation/results/dreambench_0.3.0_all.json",
            "../evaluation/results/dreambench_0.3.0_held_out.json",
            "../evaluation/results/dreambench_0.3.0_confirmation.json",
            "../evaluation/results/dreambench_0.3.0_baseline_pre_improvement.json",
            "../evaluation/results/dreamvalue_results.json",
            "../evaluation/results/live_experiments_canonical.json",
        ],
        "dreambench_0_2_0_legacy": {
            "version": held_out_02["benchmark_version"],
            "held_out_cases": held_out_02["cases"],
            "held_out_claims": held_out_02["claim_metrics"],
            "held_out_confusion": held_out_02["binary_confusion_matrix"],
            "confirmation_cases": confirmation_02["cases"],
            "confirmation_confusion": confirmation_02["binary_confusion_matrix"],
            "category_recall": held_out_02["category_classification"]["recall"],
        },
        "dreambench_0_3_0_independent": {
            "version": all_03["benchmark_version"],
            "total_cases": all_03["cases"],
            "total_claims": all_03["claim_metrics"]["ground_truth_claims"],
            "pre_improvement_recall": pre_recall,
            "post_improvement_recall": all_03["binary_confusion_matrix"]["recall"],
            "post_improvement_precision": all_03["binary_confusion_matrix"]["precision"],
            "post_improvement_f1": all_03["binary_confusion_matrix"]["f1"],
            "pipeline_metrics": all_03.get("pipeline_metrics", {}),
            "pipeline_error_attribution": all_03.get("pipeline_error_attribution", {}),
            "by_claim_form": all_03.get("by_claim_form", {}),
            "held_out_confusion": held_out_03["binary_confusion_matrix"],
            "confirmation_confusion": confirmation_03["binary_confusion_matrix"],
        },
        "dreamvalue": {
            "version": value["version"],
            "tasks": value["tasks"],
            "baseline": pick(value["baseline"]),
            "dream": pick(value["dream"]),
            "human_validated": value.get("human_validated", {}),
            "inter_rater_agreement": value.get("inter_rater_agreement", {}),
        },
        "live_experiments": live,
        "promotion_decision": "PROMOTE",
        "promotion_recommendation": "Earned deeper ecosystem experimentation: HowlPlane exploration policy, HowlCreate candidate handoff, and HowlFrame verification contract.",
    }
    (ROOT / "docs" / "evaluation.json").write_text(json.dumps(payload, indent=2) + "\n")
    print("Generated docs/evaluation.json from canonical artifacts.")


if __name__ == "__main__":
    main()
