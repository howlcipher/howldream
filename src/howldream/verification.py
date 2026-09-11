"""Limited deterministic checks against operator-supplied evidence, never truth by vote."""

import operator
import re
from fractions import Fraction

from howldream.schema import Evidence

TAXONOMY = {
    name: "1"
    for name in (
        "FABRICATION",
        "UNSUPPORTED_CLAIM",
        "FALSE_PREMISE_ACCEPTANCE",
        "CONTRADICTION",
        "SOURCE_MISATTRIBUTION",
        "OVERCONFIDENCE",
        "UNCERTAINTY_FAILURE",
        "SEMANTIC_DRIFT",
        "CONTEXT_OMISSION",
        "CONTEXT_DISTORTION",
        "NUMERIC_ERROR",
        "CAUSAL_OVERREACH",
        "TOOL_RESULT_MISINTERPRETATION",
        "MODEL_DISAGREEMENT",
        "RETRIEVAL_GROUNDING_FAILURE",
    )
}


def extract(text: str, candidate_id: str) -> list[dict]:
    claims: list[dict] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(
            r"(FACT|PREMISE|CITE|CALC|DRIFT|UNKNOWN|CONFLICT|IDEA|ASSUMPTION):\s*(.+)", line.strip()
        )
        kind, value = match.groups() if match else ("PROSE", line.strip())
        claims.append(
            {
                "id": f"{candidate_id}/claim/{len(claims) + 1}",
                "candidate_id": candidate_id,
                "kind": kind,
                "text": value,
                "status": "UNVERIFIED",
                "extractor": "line_grammar/v1",
            }
        )
    return claims


def extract_natural(text: str, candidate_id: str) -> list[dict]:
    """Extract a small observable subset of prose without consulting annotations."""
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]
    claims: list[dict] = []
    for sentence in sentences:
        kind, value = "PROSE", sentence
        citation = re.search(r"\bcites\s+([a-zA-Z0-9_./-]+)", sentence)
        calculation = re.search(
            r"(-?\d+(?:\.\d+)?)\s*([+*\-/])\s*(-?\d+(?:\.\d+)?)\s*=\s*(-?\d+(?:\.\d+)?)",
            sentence,
        )
        unknown = re.search(
            r"\bthe\s+([a-z][a-z ]+?)\s+cannot be determined\b",
            sentence,
            re.IGNORECASE,
        )
        assertion = re.search(
            r"\bthat\s+([a-z][a-z ]+?)\s+is\s+([a-z0-9][a-z0-9 ]+?)[.,]?(?:\s+and\b|$)",
            sentence,
            re.IGNORECASE,
        )
        if assertion is None:
            assertion = re.search(
                r"^The\s+([a-z][a-z ]+?)\s+is\s+([a-z0-9][a-z0-9 ]+?)[.]?$",
                sentence,
                re.IGNORECASE,
            )
        if citation:
            kind, value = "CITE", citation.group(1)
        elif calculation:
            kind = "CALC"
            value = (
                f"{calculation.group(1)} {calculation.group(2)} "
                f"{calculation.group(3)} = {calculation.group(4)}"
            )
        elif unknown:
            kind, value = "UNKNOWN", unknown.group(1).strip().replace(" ", "_")
        elif assertion:
            key = assertion.group(1).strip().replace(" ", "_")
            answer = assertion.group(2).strip().replace(" ", "_")
            kind, value = "FACT", f"{key}={answer}"
        claims.append(
            {
                "id": f"{candidate_id}/claim/{len(claims) + 1}",
                "candidate_id": candidate_id,
                "kind": kind,
                "text": value,
                "surface": sentence,
                "status": "UNVERIFIED",
                "extractor": "sentence_patterns/v1",
            }
        )
    return claims


def verify(claims: list[dict], evidence: list[Evidence]) -> list[dict]:
    facts: dict[str, list[tuple[str, str]]] = {}
    for source in evidence:
        for key, value in source.facts.items():
            facts.setdefault(key, []).append((source.id, value))
    results = []
    for claim in claims:
        kind, text = claim["kind"], claim["text"]
        status, failures, sources = "UNCERTAIN", [], []
        note = "No available check establishes this proposition."
        if kind in {"FACT", "PREMISE", "DRIFT"}:
            key, separator, value = text.partition("=")
            records = facts.get(key.strip(), [])
            values = {v for _, v in records}
            sources = [s for s, _ in records]
            if not separator:
                note = "Malformed fact; use key=value."
            elif len(values) > 1:
                status, failures = "CONTRADICTED", ["CONTRADICTION"]
                note = "Supplied evidence conflicts; a single asserted value is unjustified."
            elif not values:
                status, failures = "UNSUPPORTED", ["UNSUPPORTED_CLAIM", "UNCERTAINTY_FAILURE"]
                note = "Key absent from supplied fact ledger; absence is not proof of falsity."
            elif value.strip() in values:
                status = "SUPPORTED"
                note = "Exact match to supplied fact ledger, not independent external verification."
            else:
                status = "CONTRADICTED"
                failures = [
                    {"PREMISE": "FALSE_PREMISE_ACCEPTANCE", "DRIFT": "SEMANTIC_DRIFT"}.get(
                        kind, "CONTRADICTION"
                    )
                ]
                note = "Value differs from supplied fact ledger."
        elif kind == "CITE":
            sources = [s.id for s in evidence if s.id == text]
            status = "SUPPORTED" if sources else "UNSUPPORTED"
            failures = [] if sources else ["SOURCE_MISATTRIBUTION"]
            note = (
                "Source ID presence only; existence on the internet and entailment are not checked."
            )
        elif kind == "CALC":
            match = re.fullmatch(
                r"(-?\d{1,12}(?:\.\d{1,8})?)\s*([+*\-/])\s*"
                r"(-?\d{1,12}(?:\.\d{1,8})?)\s*=\s*(-?\d{1,24}(?:\.\d{1,8})?)",
                text,
            )
            if match:
                left, op, right, expected = match.groups()
                a, b, c = Fraction(left), Fraction(right), Fraction(expected)
                if op == "/" and b == 0:
                    note = "Division by zero is undefined."
                else:
                    actual = {
                        "+": operator.add,
                        "-": operator.sub,
                        "*": operator.mul,
                        "/": operator.truediv,
                    }[op](a, b)
                    status = "SUPPORTED" if actual == c else "CONTRADICTED"
                    failures = [] if actual == c else ["NUMERIC_ERROR"]
                    note = f"Exact rational arithmetic result: {actual}."
        elif kind == "CONFLICT":
            records = facts.get(text, [])
            if len({v for _, v in records}) > 1:
                status, sources = "SUPPORTED", [s for s, _ in records]
                note = "Correctly identifies conflicting supplied facts."
        elif kind == "UNKNOWN":
            note = "Explicit abstention; not counted as a detected failure or a verified fact."
        elif kind == "PROSE":
            note = "Unstructured prose remains unverified; claim extraction coverage is incomplete."
        results.append(
            {
                "claim_id": claim["id"],
                "candidate_id": claim["candidate_id"],
                "status": status,
                "classifications": failures,
                "source_ids": sources,
                "verifier": "supplied_ledger_and_arithmetic/v1",
                "scorer_type": "deterministic",
                "note": note,
            }
        )
    return results
