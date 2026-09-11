"""Automated regression tests preventing evidence drift and enforcing
Milestone 3.1 integrity rules.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "evaluation" / "results"
DOCS = ROOT / "docs"


def test_manifest_schema_and_promotion_decision():
    manifest_file = RESULTS / "milestone_three_manifest.json"
    assert manifest_file.exists(), "Manifest file must exist"
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert data["schema"] == "howldream.milestone_manifest/v1"
    assert data["milestone"] == "3.1"
    assert data["promotion_decision"] == "PROMOTE WITH CONDITIONS"
    assert len(data["promotion_conditions"]) >= 3
    assert any("human" in c.lower() for c in data["promotion_conditions"])

    # Ensure no artifact claims genuine human evaluation
    for artifact in data["artifacts"]:
        assert artifact.get("human_evaluated") is False


def test_live_generation_scopes_consistency():
    live_file = RESULTS / "live_experiments_canonical.json"
    assert live_file.exists()
    live = json.loads(live_file.read_text(encoding="utf-8"))

    scopes = live["generation_scopes"]
    assert scopes["fair_comparison_generations"] == 60
    assert scopes["multi_trial_generations"] == 24
    assert scopes["multi_model_generations"] == 12
    assert scopes["structured_task_generations"] == 96
    assert scopes["divergence_frontier_generations"] == 18
    assert scopes["prompt_variation_generations"] == 9
    assert scopes["diminishing_returns_generations"] == 10
    assert scopes["auxiliary_exploratory_generations"] == 37
    assert scopes["total_live_generations"] == 133

    # Check raw file matches structured count
    raw_cands = json.loads((RESULTS / "live_candidates_raw.json").read_text(encoding="utf-8"))
    assert len(raw_cands) == 96


def test_zero_denominator_rule_enforced():
    live = json.loads((RESULTS / "live_experiments_canonical.json").read_text(encoding="utf-8"))
    fair = live["fair_comparison"]
    baseline_yield = fair["baseline"]["useful_candidates_per_10k_tokens"]
    dream_yield = fair["dream"]["useful_candidates_per_10k_tokens"]

    assert baseline_yield == 0.0
    assert dream_yield == 100.2

    comp = fair["comparison"]
    assert comp["useful_yield_multiplicative_ratio"] is None
    assert comp["useful_yield_per_10k_tokens_delta"] == 100.2
    assert "Zero-Denominator Rule" in comp["zero_denominator_note"]


def test_fair_comparison_cluster_consistency():
    live = json.loads((RESULTS / "live_experiments_canonical.json").read_text(encoding="utf-8"))
    fair = live["fair_comparison"]
    assert fair["baseline"]["unique_conceptual_clusters"] == 12
    assert fair["dream"]["unique_conceptual_clusters"] == 12
    assert fair["comparison"]["conceptual_cluster_delta"] == 0
    assert fair["comparison"]["conceptual_cluster_percentage_delta"] == 0.0


def test_evaluator_provenance_not_human():
    live = json.loads((RESULTS / "live_experiments_canonical.json").read_text(encoding="utf-8"))
    eval_review = live["evaluator_review"]
    assert eval_review["provenance_classification"] == "SIMULATED_PERSONA"
    assert eval_review["human_evaluated"] is False
    for rater in eval_review["reviewers"]:
        assert rater["human"] is False
        assert rater["reviewer_type"] == "SIMULATED_PERSONA"

    site_eval = json.loads((DOCS / "evaluation.json").read_text(encoding="utf-8"))
    dv = site_eval["dreamvalue"]
    assert dv["reviewer_provenance"] == "SIMULATED_PERSONA"
    assert dv["human_evaluated"] is False


def test_divergence_frontier_verdict():
    live = json.loads((RESULTS / "live_experiments_canonical.json").read_text(encoding="utf-8"))
    frontier = live["divergence_frontier"]
    assert frontier["verdict"] == "FRONTIER NOT YET DEMONSTRATED"
    for row in frontier["data"]:
        assert row["unsupported_claim_count"] == 0
        assert row["unsupported_rate"] == 0.0


def test_pre_improvement_confusion_matrix():
    pre_file = RESULTS / "dreambench_0.3.0_baseline_pre_improvement.json"
    assert pre_file.exists()
    pre = json.loads(pre_file.read_text(encoding="utf-8"))

    # All-split
    pre_all = pre["all"]["binary_confusion_matrix"]
    assert pre_all["true_positives"] == 9
    assert pre_all["false_positives"] == 1
    assert pre_all["true_negatives"] == 143
    assert pre_all["false_negatives"] == 33
    assert (
        pre_all["true_positives"]
        + pre_all["false_positives"]
        + pre_all["true_negatives"]
        + pre_all["false_negatives"]
        == 186
    )
    assert round(pre_all["recall"], 4) == 0.2143
    assert round(pre_all["precision"], 4) == 0.9000
    assert round(pre_all["f1"], 4) == 0.3462

    # Development split
    pre_dev = pre["development"]["binary_confusion_matrix"]
    assert pre_dev["true_positives"] == 4
    assert pre_dev["false_positives"] == 1
    assert pre_dev["true_negatives"] == 61
    assert pre_dev["false_negatives"] == 14
    assert (
        pre_dev["true_positives"]
        + pre_dev["false_positives"]
        + pre_dev["true_negatives"]
        + pre_dev["false_negatives"]
        == 80
    )
    assert round(pre_dev["recall"], 4) == 0.2222


def test_site_evaluation_consistency():
    site_eval = json.loads((DOCS / "evaluation.json").read_text(encoding="utf-8"))
    live = json.loads((RESULTS / "live_experiments_canonical.json").read_text(encoding="utf-8"))

    assert site_eval["schema"] == "howldream.site_evaluation/v3"
    assert site_eval["promotion_decision"] == "PROMOTE WITH CONDITIONS"
    assert (
        site_eval["live_experiments"]["fair_comparison"]["baseline"]["unique_conceptual_clusters"]
        == live["fair_comparison"]["baseline"]["unique_conceptual_clusters"]
    )
    assert (
        site_eval["live_experiments"]["fair_comparison"]["dream"]["unique_conceptual_clusters"]
        == live["fair_comparison"]["dream"]["unique_conceptual_clusters"]
    )


def test_presentation_documents_prohibit_stale_contradictions():
    """Verify that README, index.html, and milestone_three_report do not contain
    contradictory claims.
    """
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    index_text = (DOCS / "index.html").read_text(encoding="utf-8")
    report_text = (DOCS / "milestone_three_report.md").read_text(encoding="utf-8")

    # None should claim 3.37x or 47.2 on fair comparison
    for doc_name, text in [
        ("README.md", readme_text),
        ("index.html", index_text),
        ("milestone_three_report.md", report_text),
    ]:
        assert "47.2" not in text, f"{doc_name} contains stale 47.2 metric"
        assert not re.search(r"3\.37x higher useful candidate yield", text), (
            f"{doc_name} contains stale 3.37x yield ratio"
        )

    # Must state PROMOTE WITH CONDITIONS
    assert "PROMOTE WITH CONDITIONS" in readme_text
    assert "PROMOTE WITH CONDITIONS" in index_text
    assert "PROMOTE WITH CONDITIONS" in report_text
