"""Lexical measurements and explicitly heuristic investigation triage."""

import re
from itertools import combinations
from typing import Protocol

STOP_WORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "of",
    "for",
    "to",
    "in",
    "on",
    "with",
    "by",
    "from",
    "that",
    "this",
    "is",
    "are",
    "be",
    "as",
    "it",
    "its",
    "do",
    "does",
    "not",
    "one",
    "another",
    "using",
    "use",
    "idea",
    "assumption",
}


class Scorer(Protocol):
    name: str
    scorer_type: str

    def score(self, text: str, references: list[str]) -> float: ...


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def distance(a: str, b: str) -> float:
    left, right = tokens(a), tokens(b)
    return 1 - len(left & right) / len(left | right) if left | right else 0.0


class LexicalNovelty:
    name = "lexical_novelty"
    scorer_type = "heuristic"

    def score(self, text: str, references: list[str]) -> float:
        return min((distance(text, ref) for ref in references), default=0.0)


def score_group(
    candidates: list[dict],
    baseline: list[dict],
    verification: list[dict] | None = None,
    objective: str = "",
) -> list[dict]:
    scores = []
    for i, candidate in enumerate(candidates):
        text = candidate["text"]
        duplicate = next(
            (c["id"] for c in candidates[:i] if distance(text, c["text"]) <= 0.15), None
        )
        checks = [v for v in verification or [] if v["candidate_id"] == candidate["id"]]
        failures = sum(bool(v["classifications"]) for v in checks)
        blocking = sum(
            v["status"] == "CONTRADICTED"
            or (bool(v.get("critical")) and bool(v["classifications"]))
            for v in checks
        )
        unresolved = sum(v["status"] == "UNCERTAIN" for v in checks)
        supported = sum(v["status"] == "SUPPORTED" for v in checks)
        false_premise_rejections = sum(bool(v.get("false_premise_rejected")) for v in checks)
        relevant = bool((tokens(objective) & tokens(text)) - STOP_WORDS) if objective else True
        proposal = any(line.startswith("IDEA:") for line in text.splitlines())
        decision = (
            "REJECT"
            if blocking or duplicate or not relevant
            else "INVESTIGATE"
            if proposal or false_premise_rejections > 0
            else "UNCERTAIN"
        )
        scores.append(
            {
                "candidate_id": candidate["id"],
                "duplicate_of": duplicate,
                "cluster_id": duplicate or candidate["id"],
                "novelty": {
                    "value": LexicalNovelty().score(text, [c["text"] for c in baseline]),
                    "scorer_type": "heuristic",
                },
                "relevance": {
                    "value": relevant,
                    "scorer_type": "heuristic",
                    "method": "objective_content_token_overlap",
                },
                "failure_count": failures,
                "blocking_failure_count": blocking,
                "claim_status_counts": {
                    status: sum(v["status"] == status for v in checks)
                    for status in ("SUPPORTED", "ECHO", "CONTRADICTED", "UNCERTAIN", "UNSUPPORTED")
                },
                "citation_error_count": sum(
                    "SOURCE_MISATTRIBUTION" in v["classifications"] for v in checks
                ),
                "unresolved_count": unresolved,
                "measurement_version": 2,
                "supported_count": supported,
                "false_premise_rejection_count": false_premise_rejections,
                "measurement_type": "deterministic",
                "decision": decision,
                "decision_type": "heuristic",
                "reason": (
                    "Contradiction/critical failure, duplicate, or missing lexical relevance."
                    if decision == "REJECT"
                    else (
                        (
                            f"Proposal merits investigation; successfully rejected "
                            f"{false_premise_rejections} false premise(s)."
                        )
                        if false_premise_rejections > 0
                        else (
                            "Proposal merits investigation only; "
                            "feasibility and assumptions remain unverified."
                        )
                    )
                ),
            }
        )
    return scores


def metrics(candidates: list[dict], verification: list[dict]) -> dict:
    pairs = list(combinations(candidates, 2))
    failures = {v["candidate_id"] for v in verification if v["classifications"]}
    ids = {c["id"] for c in candidates}
    checks = [v for v in verification if v["candidate_id"] in ids]
    return {
        "candidates": len(candidates),
        "lexical_diversity": (
            sum(distance(a["text"], b["text"]) for a, b in pairs) / len(pairs) if pairs else 0.0
        ),
        "exact_unique": len({c["text"] for c in candidates}),
        "claims": len(checks),
        "unresolved_claims": sum(v["status"] == "UNCERTAIN" for v in checks),
        "supported_claims": sum(v["status"] == "SUPPORTED" for v in checks),
        "measurement_version": 2,
        "supported_count": sum(v["status"] == "SUPPORTED" for v in checks),
        "echo_count": sum(v["status"] == "ECHO" for v in checks),
        "contradicted_count": sum(v["status"] == "CONTRADICTED" for v in checks),
        "uncertain_count": sum(v["status"] in {"UNCERTAIN", "UNSUPPORTED"} for v in checks),
        "false_premise_rejection_count": sum(bool(v.get("false_premise_rejected")) for v in checks),
        "false_premise_acceptance_count": sum(
            "FALSE_PREMISE_ACCEPTANCE" in v.get("classifications", []) for v in checks
        ),
        "failure_candidates": sum(c["id"] in failures for c in candidates),
        "failure_rate": (
            sum(c["id"] in failures for c in candidates) / len(candidates) if candidates else None
        ),
        "scorer_type": "deterministic",
        "scope": "lexical distance and known-check failures only",
    }
