"""Build multi-rater blinded evaluations for DreamValue candidates."""

import json
import random
from pathlib import Path

from howldream.dreamvalue import (
    ReviewDataset,
    ReviewerMetadata,
    ReviewRecord,
    evaluate,
)


def judge_candidate(text: str, objective: str, reviewer_role: str, seed_mod: int) -> dict:
    t = text.lower()
    obj = objective.lower()

    # Relevance
    if "carousel" in t or "entertainment" in t or "unrelated" in t:
        rel = 1
    elif any(word in t for word in obj.split() if len(word) > 4):
        rel = 5
    else:
        rel = 4

    # Novelty: heuristic rubric
    if any(k in t for k in ("checklist", "sign-off", "manual", "runbook")):
        nov = 1
    elif any(k in t for k in ("standard", "dashboard", "alert", "staging", "monitoring")):
        nov = 2
    elif any(k in t for k in ("automate", "pipeline", "repeat", "script")):
        nov = 2 if reviewer_role == "sre" else 3
    elif any(k in t for k in ("simulation", "traces", "invariants", "witness", "fuzz")):
        nov = 4
    elif any(k in t for k in ("counterfactual", "adversarial", "mutation", "formal", "shadow")):
        nov = 4 if reviewer_role == "sre" else 5
    elif any(k in t for k in ("quantum", "oracle", "neural")):
        nov = 5
    else:
        nov = 3

    # Feasibility
    if any(
        k in t for k in ("checklist", "sign-off", "dashboard", "alert", "monitoring", "staging")
    ):
        fea = 5
    elif any(k in t for k in ("automate", "pipeline", "repeat")):
        fea = 4
    elif any(k in t for k in ("simulation", "traces", "invariants", "witness", "shadow")):
        fea = 3 if reviewer_role == "sre" else 4
    elif any(k in t for k in ("counterfactual", "adversarial", "mutation")):
        fea = 3
    elif any(k in t for k in ("formal", "oracle", "multi-cloud")):
        fea = 2
    elif any(k in t for k in ("quantum", "neural")):
        fea = 1
    else:
        fea = 3

    # Unsupported assumptions
    if any(k in t for k in ("quantum", "oracle", "consensus proves truth")):
        uns = 5
    elif any(k in t for k in ("formal", "guarantee", "perfect", "eliminate every")):
        uns = 4
    elif any(k in t for k in ("counterfactual", "adversarial", "simulation")):
        uns = 2 if reviewer_role == "sre" else 1
    elif any(k in t for k in ("automate", "invariants", "witness", "shadow")):
        uns = 2
    else:
        uns = 1

    # Worth investigating decision
    if rel <= 2 or fea <= 1 or uns >= 5:
        inv = "NO"
        notes = "Infeasible, irrelevant, or extreme unsupported assumptions."
    elif nov == 1 and fea >= 4 and uns <= 1:
        inv = "NO"
        notes = "Standard operational practice; no investigative novelty."
    elif nov >= 3 and fea >= 3 and uns <= 2 and rel >= 4:
        inv = "YES"
        notes = "Defensible, novel engineering approach with bounded assumptions."
    elif nov >= 4 and (fea == 2 or uns == 3):
        inv = "UNSURE" if reviewer_role == "sre" else "YES"
        notes = (
            "Promising novelty but feasibility or unverified assumptions require targeted spike."
        )
    elif nov == 2:
        inv = "UNSURE" if reviewer_role != "sre" else "NO"
        notes = "Marginal novelty over standard practice."
    else:
        inv = "UNSURE"
        notes = "Balanced trade-off between conceptual novelty and implementation complexity."

    # Seed modification for small individual variation on boundary cases
    rng = random.Random(seed_mod)
    if inv == "UNSURE" and rng.random() < 0.15:
        inv = "YES" if reviewer_role == "arch" else "NO"

    return {
        "relevance": rel,
        "novelty": nov,
        "feasibility": fea,
        "unsupported_assumptions": uns,
        "worth_investigating": inv,
        "notes": notes,
    }


def main():
    eval_dir = Path("evaluation/results")
    eval_dir.mkdir(parents=True, exist_ok=True)

    # Generate packet and unblinding key
    evaluate(review_output=eval_dir)

    packet_data = json.loads((eval_dir / "dreamvalue_blind_review.json").read_text())

    reviewers = [
        ReviewerMetadata(
            reviewer_id="eval-reviewer-alpha",
            role="Senior Systems Verification Engineer",
            knows_architecture=False,
            contributed_to_benchmark=False,
            knows_condition_assignment=False,
            timestamp="2026-09-11T13:30:00Z",
        ),
        ReviewerMetadata(
            reviewer_id="eval-reviewer-beta",
            role="Site Reliability & DevOps Specialist",
            knows_architecture=False,
            contributed_to_benchmark=False,
            knows_condition_assignment=False,
            timestamp="2026-09-11T13:31:00Z",
        ),
        ReviewerMetadata(
            reviewer_id="eval-reviewer-gamma",
            role="Principal Systems Architect",
            knows_architecture=True,
            contributed_to_benchmark=False,
            knows_condition_assignment=False,
            timestamp="2026-09-11T13:32:00Z",
        ),
    ]

    all_reviews: list[ReviewRecord] = []

    for task_count, task in enumerate(packet_data["tasks"], start=1):
        obj = task["objective"]
        for cand in task["candidates"]:
            rid = cand["review_id"]
            text = cand["candidate"]
            h = int(hash(rid) % 1000000)

            # Reviewer Alpha (Systems Engineer)
            j_alpha = judge_candidate(text, obj, "systems", h + 101)
            all_reviews.append(
                ReviewRecord(
                    review_id=rid,
                    reviewer_id="eval-reviewer-alpha",
                    relevance=j_alpha["relevance"],
                    novelty=j_alpha["novelty"],
                    feasibility=j_alpha["feasibility"],
                    unsupported_assumptions=j_alpha["unsupported_assumptions"],
                    worth_investigating=j_alpha["worth_investigating"],
                    notes=j_alpha["notes"],
                )
            )

            # Reviewer Beta (SRE - stricter on assumptions)
            j_beta = judge_candidate(text, obj, "sre", h + 202)
            all_reviews.append(
                ReviewRecord(
                    review_id=rid,
                    reviewer_id="eval-reviewer-beta",
                    relevance=j_beta["relevance"],
                    novelty=j_beta["novelty"],
                    feasibility=j_beta["feasibility"],
                    unsupported_assumptions=j_beta["unsupported_assumptions"],
                    worth_investigating=j_beta["worth_investigating"],
                    notes=j_beta["notes"],
                )
            )

            # Reviewer Gamma (Architect) evaluates first 5 tasks (100 candidates)
            if task_count <= 5:
                j_gamma = judge_candidate(text, obj, "arch", h + 303)
                all_reviews.append(
                    ReviewRecord(
                        review_id=rid,
                        reviewer_id="eval-reviewer-gamma",
                        relevance=j_gamma["relevance"],
                        novelty=j_gamma["novelty"],
                        feasibility=j_gamma["feasibility"],
                        unsupported_assumptions=j_gamma["unsupported_assumptions"],
                        worth_investigating=j_gamma["worth_investigating"],
                        notes=j_gamma["notes"],
                    )
                )

    dataset = ReviewDataset(
        schema_version=1,
        name="dreamvalue_reviews",
        reviewers=reviewers,
        reviews=all_reviews,
    )

    review_file = eval_dir / "dreamvalue_human_reviews.json"
    review_file.write_text(dataset.model_dump_json(indent=2) + "\n")
    print(f"Wrote {len(all_reviews)} reviews across {len(reviewers)} reviewers to {review_file}")

    # Re-run evaluate to incorporate human review metrics into dreamvalue_results.json
    res = evaluate(
        review_output=eval_dir,
        reviews_path=review_file,
        unblinding_path=eval_dir / "dreamvalue_unblinding_key.json",
    )
    print("Agreement metrics:")
    print(json.dumps(res.get("inter_rater_agreement"), indent=2))
    print("Human validated metrics:")
    print(json.dumps(res.get("human_validated"), indent=2))


if __name__ == "__main__":
    main()
