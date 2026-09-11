"""Versioned, split-aware reliability evaluation with explicit provenance."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from collections import defaultdict
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

from howldream.schema import Evidence
from howldream.scoring import tokens
from howldream.verification import extract_natural, verify


class BenchmarkModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ExpectedClaim(BenchmarkModel):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    text: str = Field(min_length=1, max_length=2_000)
    verification_input: str = Field(min_length=1, max_length=2_000)
    label: Literal["ACCEPTABLE", "PROBLEMATIC"]
    category: str | None = None

    @model_validator(mode="after")
    def category_matches_label(self):
        if (self.label == "PROBLEMATIC") != bool(self.category):
            raise ValueError(
                "problematic claims require a category; acceptable claims must omit it"
            )
        return self


class BenchmarkCase(BenchmarkModel):
    id: str = Field(pattern=r"^DB2-[0-9]{4}$")
    split: Literal["development", "validation", "held_out", "confirmation"]
    category: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    source: str
    origin: Literal["authored", "generated", "imported"]
    prompt: str = Field(min_length=1, max_length=5_000)
    response: str = Field(min_length=1, max_length=10_000)
    evidence: list[Evidence]
    expected_behavior: str
    expected_classification: Literal["ACCEPTABLE", "PROBLEMATIC"]
    deterministic_check: bool
    difficulty: Literal["easy", "medium", "hard"]
    notes: str
    claims: list[ExpectedClaim] = Field(min_length=1)

    @model_validator(mode="after")
    def classification_matches_claims(self):
        problematic = any(claim.label == "PROBLEMATIC" for claim in self.claims)
        if problematic != (self.expected_classification == "PROBLEMATIC"):
            raise ValueError("case classification must match its claim labels")
        return self


class BenchmarkDataset(BenchmarkModel):
    schema_version: Literal[1]
    name: Literal["dreambench"]
    version: str = Field(pattern=r"^0\.[0-9]+\.[0-9]+$")
    published: str
    provenance: str
    cases: list[BenchmarkCase] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids_and_splits(self):
        ids = [case.id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("benchmark case IDs must be unique")
        required = {"development", "validation", "held_out", "confirmation"}
        if {case.split for case in self.cases} != required:
            raise ValueError(
                "development, validation, held_out, and confirmation splits are required"
            )
        return self


def dataset_path() -> Path:
    return Path(str(files("howldream").joinpath("fixtures/dreambench_v0_2_0.json")))


def load_dataset(path: Path | None = None) -> tuple[BenchmarkDataset, str]:
    target = path or dataset_path()
    raw = target.read_bytes()
    if len(raw) > 5_000_000:
        raise ValueError("benchmark dataset exceeds 5 MB")
    return BenchmarkDataset.model_validate_json(raw), hashlib.sha256(raw).hexdigest()


def _similarity(left: str, right: str) -> float:
    a, b = tokens(left), tokens(right)
    return len(a & b) / len(a | b) if a | b else 0.0


def _match_claims(
    expected: list[ExpectedClaim], extracted: list[str]
) -> tuple[dict[str, int], set[int]]:
    matches: dict[str, int] = {}
    used: set[int] = set()
    for claim in expected:
        ranked = sorted(
            (
                (_similarity(claim.text, text), index)
                for index, text in enumerate(extracted)
                if index not in used
            ),
            reverse=True,
        )
        if ranked and ranked[0][0] >= 0.45:
            matches[claim.id] = ranked[0][1]
            used.add(ranked[0][1])
    return matches, used


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def confusion(rows: list[dict]) -> dict:
    tp = sum(row["expected_problematic"] and row["predicted_problematic"] for row in rows)
    fp = sum(not row["expected_problematic"] and row["predicted_problematic"] for row in rows)
    tn = sum(not row["expected_problematic"] and not row["predicted_problematic"] for row in rows)
    fn = sum(row["expected_problematic"] and not row["predicted_problematic"] for row in rows)
    precision, recall = _ratio(tp, tp + fp), _ratio(tp, tp + fn)
    return {
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": (
            2 * precision * recall / (precision + recall)
            if precision is not None and recall is not None and precision + recall
            else None
        ),
        "specificity": _ratio(tn, tn + fp),
        "false_positive_rate": _ratio(fp, fp + tn),
        "false_negative_rate": _ratio(fn, fn + tp),
        "accuracy": _ratio(tp + tn, len(rows)),
    }


def _git_sha() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _git_dirty() -> bool | None:
    result = subprocess.run(["git", "diff", "--quiet"], capture_output=True, text=True, check=False)
    return result.returncode != 0 if result.returncode in {0, 1} else None


def _implementation_hash() -> str:
    from howldream import verification

    content = Path(__file__).read_bytes() + Path(verification.__file__).read_bytes()
    return hashlib.sha256(content).hexdigest()


def benchmark(
    split: str = "development", output: Path | None = None, dataset: Path | None = None
) -> dict:
    """Run one deterministic split; development is intentionally the default."""
    started = time.monotonic()
    definition, dataset_hash = load_dataset(dataset)
    if split not in {"development", "validation", "held_out", "confirmation", "all"}:
        raise ValueError("split must be development, validation, held_out, confirmation, or all")
    cases = [case for case in definition.cases if split == "all" or case.split == split]
    if not cases:
        raise ValueError(f"benchmark split contains no cases: {split}")
    case_rows: list[dict[str, Any]] = []
    claim_rows: list[dict[str, Any]] = []
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    extracted_total = matched_total = spurious_total = 0
    for case in cases:
        extracted_claims = extract_natural(case.response, case.id)
        extracted_text = [claim["surface"] for claim in extracted_claims]
        matches, used = _match_claims(case.claims, extracted_text)
        extracted_total += len(extracted_text)
        matched_total += len(matches)
        spurious_total += len(extracted_text) - len(used)
        predicted_categories: set[str] = set()
        for expected in case.claims:
            detected: list[str] = []
            status = "MISSED_BY_EXTRACTOR"
            if expected.id in matches:
                observed = extracted_claims[matches[expected.id]]
                checked = verify([observed], case.evidence)
                detected = sorted(
                    {label for result in checked for label in result["classifications"]}
                )
                status = checked[0]["status"] if checked else "UNRESOLVED"
                predicted_categories.update(detected)
            predicted = bool(detected)
            row: dict[str, Any] = {
                "case_id": case.id,
                "claim_id": expected.id,
                "category": expected.category or "CONTROL",
                "expected_problematic": expected.label == "PROBLEMATIC",
                "predicted_problematic": predicted,
                "extracted": expected.id in matches,
                "verification_outcome": status,
                "detected_categories": detected,
            }
            claim_rows.append(row)
            by_category[row["category"]].append(row)
        case_rows.append(
            {
                "id": case.id,
                "split": case.split,
                "category": case.category,
                "severity": case.severity,
                "expected": case.expected_classification,
                "predicted": "PROBLEMATIC" if predicted_categories else "ACCEPTABLE",
                "detected_categories": sorted(predicted_categories),
            }
        )
    ground_truth = len(claim_rows)
    report = {
        "schema": "howldream.dreambench_run/v2",
        "suite": "dreambench",
        "benchmark_version": definition.version,
        "split": split,
        "held_out_execution": split in {"held_out", "confirmation", "all"},
        "dataset_hash": dataset_hash,
        "code_sha": _git_sha(),
        "code_dirty": _git_dirty(),
        "implementation_hash": _implementation_hash(),
        "timestamp": datetime.now(UTC).isoformat(),
        "scorers": [
            {
                "scorer": "token_set_claim_match",
                "scorer_type": "heuristic",
                "version": "1",
                "configuration": {"threshold": 0.45},
            },
            {
                "scorer": "supplied_ledger_and_arithmetic",
                "scorer_type": "deterministic",
                "version": "1",
                "configuration": {},
            },
        ],
        "cases": len(cases),
        "case_ids": [case.id for case in cases],
        "claim_metrics": {
            "ground_truth_claims": ground_truth,
            "extracted_relevant_claims": matched_total,
            "missed_claims": ground_truth - matched_total,
            "spurious_extractions": spurious_total,
            "coverage": _ratio(matched_total, ground_truth),
            "approximate_precision": _ratio(matched_total, extracted_total),
            "matching_is_heuristic": True,
        },
        "binary_confusion_matrix": confusion(claim_rows),
        "by_category": {name: confusion(rows) for name, rows in sorted(by_category.items())},
        "category_confusion": {
            category: confusion(
                [
                    {
                        "expected_problematic": row["category"] == category,
                        "predicted_problematic": category in row["detected_categories"],
                    }
                    for row in claim_rows
                    if row["expected_problematic"]
                ]
            )
            for category in sorted(name for name in by_category if name != "CONTROL")
        },
        "category_classification": {
            "problematic_claims": sum(row["expected_problematic"] for row in claim_rows),
            "correct_category": sum(
                row["expected_problematic"] and row["category"] in row["detected_categories"]
                for row in claim_rows
            ),
            "recall": _ratio(
                sum(
                    row["expected_problematic"] and row["category"] in row["detected_categories"]
                    for row in claim_rows
                ),
                sum(row["expected_problematic"] for row in claim_rows),
            ),
            "overlapping_categories": True,
        },
        "case_results": case_rows,
        "claim_results": claim_rows,
        "errors": [],
        "excluded_cases": [],
        "elapsed_seconds": time.monotonic() - started,
        "limitations": [
            "Authored and template-derived cases evaluate narrow supplied-evidence checks.",
            "Sentence extraction matching is heuristic and is not semantic entailment.",
            "UNRESOLVED is not treated as false; unsupported checks require available evidence.",
        ],
        "passed": True,
    }
    if output:
        output.mkdir(parents=True, exist_ok=True)
        target = output / f"dreambench_{definition.version}_{split}.json"
        target.write_text(json.dumps(report, indent=2) + "\n")
        matrix = cast(dict[str, Any], report["binary_confusion_matrix"])
        markdown = [
            f"# DreamBench {definition.version}: {split}",
            "",
            f"Dataset SHA-256: `{dataset_hash}`",
            "",
            "| TP | FP | TN | FN | Precision | Recall | F1 |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            "| {tp} | {fp} | {tn} | {fn} | {precision} | {recall} | {f1} |".format(
                tp=matrix["true_positives"],
                fp=matrix["false_positives"],
                tn=matrix["true_negatives"],
                fn=matrix["false_negatives"],
                precision=(
                    f"{matrix['precision']:.4f}" if matrix["precision"] is not None else "n/a"
                ),
                recall=(f"{matrix['recall']:.4f}" if matrix["recall"] is not None else "n/a"),
                f1=f"{matrix['f1']:.4f}" if matrix["f1"] is not None else "n/a",
            ),
            "",
            (
                "Claim extraction matching is heuristic. Verification is limited to "
                "the supplied ledger, source-ID presence, and exact arithmetic."
            ),
            "",
        ]
        (output / f"dreambench_{definition.version}_{split}.md").write_text("\n".join(markdown))
    return report


def list_benchmarks() -> dict:
    definition, digest = load_dataset()
    names = ("development", "validation", "held_out", "confirmation")
    splits = {name: sum(case.split == name for case in definition.cases) for name in names}
    return {
        "benchmarks": [
            {
                "name": definition.name,
                "version": definition.version,
                "cases": len(definition.cases),
                "splits": splits,
                "dataset_hash": digest,
            }
        ]
    }
