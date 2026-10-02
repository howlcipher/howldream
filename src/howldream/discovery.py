"""Advisory concept-normalized clustering, anchoring and compact diversity memory.

No embeddings or extra inference. Similarity is a transparent lexical heuristic,
with a small synonym map; these ratios are not calibrated semantic measurements.
"""

import re
from collections import Counter
from collections.abc import Sequence
from hashlib import sha256
from itertools import pairwise

from howldream.scoring import STOP_WORDS, tokens

ALIASES = {
    "detect": "detection",
    "detector": "detection",
    "detecting": "detection",
    "monitor": "observation",
    "monitoring": "observation",
    "observe": "observation",
    "forecast": "prediction",
    "predict": "prediction",
    "predictive": "prediction",
    "schedule": "scheduling",
    "schedules": "scheduling",
    "calendars": "scheduling",
    "tired": "fatigue",
    "exhaustion": "fatigue",
    "workloads": "workload",
    "developers": "developer",
    "engineers": "developer",
    "engineering": "developer",
    "queues": "queue",
    "tests": "test",
    "templates": "template",
    "environments": "environment",
    "signals": "signal",
    "images": "image",
    "duplicated": "duplicate",
    "misses": "miss",
    "flakiness": "flaky",
    "costs": "cost",
    "spend": "cost",
    "expenses": "cost",
}
BOILERPLATE = STOP_WORDS | {
    "build",
    "create",
    "software",
    "tool",
    "system",
    "team",
    "platform",
    "unconventional",
    "alternative",
    "propose",
    "replace",
    "treat",
    "make",
    "offer",
    "teams",
    "proposal",
    "could",
    "would",
    "should",
    "meaningful",
    "opportunities",
}


def concept_tokens(text: str) -> set[str]:
    return {ALIASES.get(t, t) for t in tokens(text) - BOILERPLATE}


def leading_phrases(text: str, limit: int = 16) -> set[tuple[str, str]]:
    """Leading content phrases approximate problem families, not logical equivalence.

    Limit to 16 words to avoid joining ideas merely because their long explanations
    mention the same general topic. Generic subject terms cannot create a phrase link.
    """
    words = [
        ALIASES.get(t, t) for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in BOILERPLATE
    ][:limit]
    return set(pairwise(words))


def similarity(a: str, b: str) -> float:
    left, right = concept_tokens(a), concept_tokens(b)
    jaccard = len(left & right) / len(left | right) if left | right else 0.0
    phrase_link = bool(leading_phrases(a, 8) & leading_phrases(b, 8))
    return max(jaccard, 0.5 if phrase_link else 0.0)


def idea_units(candidates: list[dict]) -> list[dict]:
    units = []
    for candidate in candidates:
        offset = 0
        index = 0
        for line in candidate["text"].splitlines(keepends=True):
            if line.startswith("IDEA:"):
                index += 1
                units.append(
                    {
                        "id": f"{candidate['id']}/idea/{index}",
                        "candidate_id": candidate["id"],
                        "text": line.rstrip("\r\n"),
                        "source_span": [offset, offset + len(line.rstrip("\r\n"))],
                        "source_hash": sha256(candidate["text"].encode()).hexdigest(),
                    }
                )
            offset += len(line)
    return units


def compact_families(candidates: list[dict]) -> list[str]:
    """Short labels only, never entire prior provider output or claim ledgers."""
    labels = []
    for unit in idea_units(candidates):
        label = ", ".join(sorted(concept_tokens(unit["text"]))[:8])
        if label and label not in labels:
            labels.append(label)
    return labels[:100]


def analyze_discovery(
    candidates: list[dict],
    baseline: list[dict],
    objective: str,
    evidence: list[dict],
    explored_families: list[str],
    ranking_criteria: Sequence[str],
) -> dict:
    units = idea_units(candidates)
    clusters: list[dict] = []
    for unit in units:
        nearest = max(
            ((similarity(unit["text"], c["representative_text"]), c) for c in clusters),
            key=lambda row: row[0],
            default=None,
        )
        match = nearest[1] if nearest and nearest[0] >= 0.5 else None
        if match is None:
            match = {
                "id": f"cluster-{len(clusters) + 1}",
                "representative": unit["id"],
                "representative_text": unit["text"],
                "label": ", ".join(sorted(concept_tokens(unit["text"]))[:8]),
                "members": [],
            }
            clusters.append(match)
        unit.update(
            cluster=match["id"],
            representative=match["representative"],
            similar_to=match["representative"] if match["members"] else None,
            similarity_to_representative=nearest[0]
            if nearest and unit["id"] != match["representative"]
            else 1.0,
        )
        match["members"].append(unit["id"])
    source_texts = [e["text"] + " " + " ".join(e["facts"].values()) for e in evidence]
    source_sentences = [
        sentence for text in source_texts for sentence in re.split(r"(?<=[.!?])\s+|\n+", text)
    ]
    context_texts = source_sentences + [objective] + explored_families
    evidence_terms = set().union(*(concept_tokens(t) for t in source_texts))
    context_terms = set().union(*(concept_tokens(t) for t in context_texts))
    counts: Counter[str] = Counter()
    for unit in units:
        terms = concept_tokens(unit["text"])
        denominator = len(terms) or 1
        unit["evidence_token_overlap"] = len(terms & evidence_terms) / denominator
        unit["context_token_overlap"] = len(terms & context_terms) / denominator
        unit["evidence_family_echo"] = any(
            leading_phrases(unit["text"]) & leading_phrases(t) for t in source_sentences
        )
        unit["context_family_echo"] = any(
            leading_phrases(unit["text"]) & leading_phrases(t) for t in context_texts
        )
        counts["evidence"] += unit["evidence_token_overlap"] >= 0.6 or unit["evidence_family_echo"]
        counts["context"] += unit["context_token_overlap"] >= 0.6 or unit["context_family_echo"]
        counts["novel"] += (
            max(
                (
                    similarity(unit["text"], t)
                    for t in context_texts + [b["text"] for b in baseline]
                ),
                default=0.0,
            )
            < 0.5
        )
    n = len(units)

    def ratio(count):
        return count / n if n else None

    summary = {
        "context_echo_ratio": ratio(counts["context"]),
        "evidence_echo_ratio": ratio(counts["evidence"]),
        "novel_concept_ratio": ratio(counts["novel"]),
        "repeated_family_ratio": ratio(n - len(clusters)),
    }
    warnings = ["DISCOVERY_ANCHORING_HIGH"] if n and counts["context"] / n >= 0.6 else []
    ranking = []
    if ranking_criteria:
        for cluster in clusters:
            text = cluster["representative_text"]
            scores = {
                "novelty": 1 - max((similarity(text, b["text"]) for b in baseline), default=0.0),
                "objective_fit": similarity(text, objective),
            }
            selected = {k: scores[k] for k in ranking_criteria}
            ranking.append(
                {
                    "cluster": cluster["id"],
                    "representative": cluster["representative"],
                    "score": sum(selected.values()) / len(selected),
                    "criteria": selected,
                    "rationale": (
                        "Equal-weight concept-token overlap/distance; no execution authority"
                    ),
                }
            )
        ranking.sort(key=lambda row: row["score"], reverse=True)
    return {
        **summary,
        "idea_count": n,
        "cluster_count": len(clusters),
        "units": units,
        "clusters": clusters,
        "ranking": ranking,
        "warnings": warnings,
        "explored_families": [c["label"] for c in clusters],
        "method": (
            "concept_tokens_and_leading_phrases/v3; Jaccard cluster threshold 0.5 "
            "or first-8-content-word phrase link; echo coverage 0.6 or first-16-word phrase link"
        ),
        "measurement_type": "ADVISORY_HEURISTIC",
        "limitations": "Not semantic equivalence, calibrated novelty, entailment or usefulness",
    }
