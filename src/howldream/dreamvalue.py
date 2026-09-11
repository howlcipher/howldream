"""Transparent evaluation of useful conceptual exploration."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from collections.abc import Sequence
from importlib.resources import files
from itertools import combinations
from pathlib import Path
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from howldream.scoring import distance


class ValueModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ReviewRecord(ValueModel):
    review_id: str
    reviewer_id: str = Field(validation_alias=AliasChoices("reviewer_id", "reviewer"))
    relevance: int = Field(ge=1, le=5, validation_alias=AliasChoices("relevance", "useful"))
    novelty: int = Field(ge=1, le=5, validation_alias=AliasChoices("novelty", "novel"))
    feasibility: int = Field(ge=1, le=5, validation_alias=AliasChoices("feasibility", "feasible"))
    unsupported_assumptions: int = Field(ge=1, le=5)
    worth_investigating: Literal["YES", "NO", "UNSURE"]
    notes: str = ""


class ReviewerMetadata(ValueModel):
    reviewer_id: str
    role: str = ""
    knows_architecture: bool = False
    contributed_to_benchmark: bool = False
    knows_condition_assignment: bool = False
    timestamp: str = ""


class ReviewDataset(ValueModel):
    schema_version: Literal[1] = 1
    name: str = "dreamvalue_reviews"
    reviewers: list[ReviewerMetadata] = Field(default_factory=list)
    reviews: list[ReviewRecord] = Field(default_factory=list)


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


def cohen_kappa(
    r1: Sequence[str], r2: Sequence[str], categories: Sequence[str] | None = None
) -> float:
    if len(r1) != len(r2) or len(r1) == 0:
        return 0.0
    cats = sorted(set(r1) | set(r2) if categories is None else set(categories))
    n = len(r1)
    po = sum(a == b for a, b in zip(r1, r2)) / n
    pe = sum((r1.count(c) / n) * (r2.count(c) / n) for c in cats)
    if abs(1.0 - pe) < 1e-9:
        return 1.0 if abs(po - 1.0) < 1e-9 else 0.0
    return (po - pe) / (1.0 - pe)


def fleiss_kappa(ratings: Sequence[Sequence[str]], categories: Sequence[str]) -> float:
    n_items = len(ratings)
    if n_items == 0:
        return 0.0
    n_raters = len(ratings[0])
    if n_raters <= 1:
        return 1.0
    p_j = {c: 0 for c in categories}
    p_i = []
    for item in ratings:
        counts = {c: item.count(c) for c in categories}
        for c in categories:
            p_j[c] += counts[c]
        p_i.append(
            (sum(cnt * cnt for cnt in counts.values()) - n_raters) / (n_raters * (n_raters - 1))
        )
    p_bar = sum(p_i) / n_items
    p_e = sum((tot / (n_items * n_raters)) ** 2 for tot in p_j.values())
    if abs(1.0 - p_e) < 1e-9:
        return 1.0 if abs(p_bar - 1.0) < 1e-9 else 0.0
    return (p_bar - p_e) / (1.0 - p_e)


def compute_inter_rater_agreement(reviews: list[ReviewRecord | dict]) -> dict:
    records = [
        r if isinstance(r, ReviewRecord) else ReviewRecord.model_validate(r) for r in reviews
    ]
    by_item: dict[str, dict[str, ReviewRecord]] = defaultdict(dict)
    for r in records:
        by_item[r.review_id][r.reviewer_id] = r

    raters = sorted({r.reviewer_id for r in records})
    pairs = list(combinations(raters, 2))

    pair_metrics = {}
    kappa_list = []
    raw_agree_list = []

    for r1, r2 in pairs:
        common_items = [
            item for item, item_revs in by_item.items() if r1 in item_revs and r2 in item_revs
        ]
        if not common_items:
            continue
        c1 = [by_item[item][r1].worth_investigating for item in common_items]
        c2 = [by_item[item][r2].worth_investigating for item in common_items]

        raw_agree = sum(a == b for a, b in zip(c1, c2)) / len(c1)
        k = cohen_kappa(c1, c2, ["YES", "NO", "UNSURE"])

        ord_metrics = {}
        for dim in ("relevance", "novelty", "feasibility", "unsupported_assumptions"):
            v1 = [getattr(by_item[item][r1], dim) for item in common_items]
            v2 = [getattr(by_item[item][r2], dim) for item in common_items]
            mad = sum(abs(a - b) for a, b in zip(v1, v2)) / len(v1)
            exact = sum(a == b for a, b in zip(v1, v2)) / len(v1)
            within_1 = sum(abs(a - b) <= 1 for a, b in zip(v1, v2)) / len(v1)
            ord_metrics[dim] = {
                "mean_absolute_diff": round(mad, 4),
                "exact_agreement": round(exact, 4),
                "within_1_agreement": round(within_1, 4),
            }

        pair_metrics[f"{r1}_vs_{r2}"] = {
            "co_rated_items": len(common_items),
            "raw_agreement_worth_investigating": round(raw_agree, 4),
            "cohen_kappa_worth_investigating": round(k, 4),
            "ordinal_dimensions": ord_metrics,
        }
        kappa_list.append(k)
        raw_agree_list.append(raw_agree)

    fleiss = None
    if len(raters) >= 3:
        full_items = [
            [item_revs[r].worth_investigating for r in raters]
            for item_revs in by_item.values()
            if all(r in item_revs for r in raters)
        ]
        if full_items:
            fleiss = round(fleiss_kappa(full_items, ["YES", "NO", "UNSURE"]), 4)

    return {
        "total_raters": len(raters),
        "total_items": len(by_item),
        "multi_rated_items": sum(1 for item_revs in by_item.values() if len(item_revs) >= 2),
        "mean_cohen_kappa": round(sum(kappa_list) / len(kappa_list), 4) if kappa_list else None,
        "mean_raw_agreement": (
            round(sum(raw_agree_list) / len(raw_agree_list), 4) if raw_agree_list else None
        ),
        "fleiss_kappa_multi_rater": fleiss,
        "pairwise": pair_metrics,
    }


def human_condition_metrics(
    reviews: list[ReviewRecord | dict], unblinding_map: dict[str, dict]
) -> dict:
    records = [
        r if isinstance(r, ReviewRecord) else ReviewRecord.model_validate(r) for r in reviews
    ]
    by_item: dict[str, list[ReviewRecord]] = defaultdict(list)
    for r in records:
        by_item[r.review_id].append(r)

    cand_records = []
    for rid, revs in by_item.items():
        if rid not in unblinding_map:
            continue
        meta = unblinding_map[rid]
        rel = [r.relevance for r in revs]
        nov = [r.novelty for r in revs]
        fea = [r.feasibility for r in revs]
        uns = [r.unsupported_assumptions for r in revs]
        inv = [r.worth_investigating for r in revs]

        m_rel = sum(rel) / len(rel)
        m_nov = sum(nov) / len(nov)
        m_fea = sum(fea) / len(fea)
        m_uns = sum(uns) / len(uns)

        yes_count = inv.count("YES")
        no_count = inv.count("NO")
        consensus = (
            "YES" if yes_count > len(inv) / 2 else ("NO" if no_count > len(inv) / 2 else "UNSURE")
        )
        useful = consensus == "YES" and m_rel >= 3.5 and m_fea >= 3.0 and m_uns <= 2.5

        cand_records.append(
            {
                "review_id": rid,
                "condition": meta["condition"],
                "approach": meta.get("approach", ""),
                "relevance": m_rel,
                "novelty": m_nov,
                "feasibility": m_fea,
                "unsupported": m_uns,
                "consensus": consensus,
                "useful": useful,
            }
        )

    res: dict[str, dict[str, Any] | None] = {}
    for cond in ("baseline", "dream"):
        items = [c for c in cand_records if c["condition"] == cond]
        n = len(items)
        if n == 0:
            res[cond] = None
            continue
        inv_count = sum(1 for c in items if c["consensus"] == "YES")
        use_count = sum(1 for c in items if c["useful"])
        res[cond] = {
            "candidates": n,
            "human_relevance_mean": round(sum(c["relevance"] for c in items) / n, 4),
            "human_novelty_mean": round(sum(c["novelty"] for c in items) / n, 4),
            "human_feasibility_mean": round(sum(c["feasibility"] for c in items) / n, 4),
            "human_unsupported_mean": round(sum(c["unsupported"] for c in items) / n, 4),
            "human_investigate_count": inv_count,
            "human_investigate_rate": round(inv_count / n, 4),
            "human_useful_candidate_count": use_count,
            "human_useful_candidate_yield": round(use_count / n, 4),
        }
    return res


def evaluate(
    suite_path: Path | None = None,
    review_output: Path | None = None,
    reviews_path: Path | None = None,
    unblinding_path: Path | None = None,
) -> dict:
    suite, digest = load_suite(suite_path)
    grouped: dict[str, list[ValueCandidate]] = {
        condition: [] for condition in ("baseline", "dream")
    }
    for task in suite.tasks:
        for candidate in task.candidates:
            grouped[candidate.condition].append(candidate)
    baseline, dream = grouped["baseline"], grouped["dream"]
    divergence_curve, candidate_count_curve = _curves(dream)
    result: dict[str, Any] = {
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

    # Deterministic packet and unblinding key generation
    rng = random.Random(20260910)
    packet = []
    unblinding_map: dict[str, dict] = {}
    for task in suite.tasks:
        candidates = list(task.candidates)
        rng.shuffle(candidates)
        task_entries = []
        for index, candidate in enumerate(candidates):
            review_id = f"{task.id}-R{index + 1:02d}"
            unblinding_map[review_id] = {
                "task_id": task.id,
                "candidate_id": candidate.id,
                "condition": candidate.condition,
                "approach": candidate.approach,
                "divergence": candidate.divergence,
                "ordinal": candidate.ordinal,
            }
            task_entries.append(
                {
                    "review_id": review_id,
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
            )
        packet.append(
            {
                "task_id": task.id,
                "domain": task.domain,
                "objective": task.objective,
                "candidates": task_entries,
            }
        )

    # Ingest human reviews if available
    rev_file = reviews_path
    if (
        rev_file is None
        and review_output
        and (review_output / "dreamvalue_human_reviews.json").exists()
    ):
        rev_file = review_output / "dreamvalue_human_reviews.json"
    if rev_file is None:
        default_candidate = Path("evaluation/results/dreamvalue_human_reviews.json")
        if default_candidate.exists():
            rev_file = default_candidate

    unblind_dict = unblinding_map
    if unblinding_path and unblinding_path.exists():
        unblind_dict = json.loads(unblinding_path.read_text())

    if rev_file and rev_file.exists():
        review_data = json.loads(rev_file.read_text())
        raw_reviews = (
            review_data.get("reviews", review_data)
            if isinstance(review_data, dict)
            else review_data
        )
        agreement = compute_inter_rater_agreement(raw_reviews)
        human_metrics = human_condition_metrics(raw_reviews, unblind_dict)
        result["inter_rater_agreement"] = agreement
        result["human_validated"] = human_metrics
        result["methodology"]["human_review"] = {
            "blinded": True,
            "raters": agreement.get("total_raters", 0),
            "mean_kappa": agreement.get("mean_cohen_kappa"),
            "mean_agreement": agreement.get("mean_raw_agreement"),
        }

    if review_output:
        review_output.mkdir(parents=True, exist_ok=True)
        packet_data = {
            "schema": "howldream.human_review/v1",
            "blinded": True,
            "supports_independent_reviewers": True,
            "tasks": packet,
        }
        (review_output / "dreamvalue_blind_review.json").write_text(
            json.dumps(packet_data, indent=2) + "\n"
        )
        (review_output / "dreamvalue_unblinding_key.json").write_text(
            json.dumps(unblinding_map, indent=2) + "\n"
        )
        (review_output / "dreamvalue_results.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
