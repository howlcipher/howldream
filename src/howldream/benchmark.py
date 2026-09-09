"""Balanced authored regression fixtures, not a general detection benchmark."""

import json
import time
from importlib.resources import files

from howldream.schema import Evidence
from howldream.verification import extract, verify


def benchmark() -> dict:
    started = time.monotonic()
    fixtures = json.loads(files("howldream").joinpath("fixtures/dreambench.json").read_text())
    counts = dict.fromkeys(
        ["true_positives", "false_positives", "true_negatives", "false_negatives"], 0
    )
    results = []
    for fixture in fixtures:
        evidence = [Evidence(id="supplied", facts=fixture["facts"])]
        if "conflict" in fixture:
            evidence.append(Evidence(id="conflicting", facts=fixture["conflict"]))
        actual = verify(extract(fixture["text"], fixture["id"]), evidence)
        detected = {label for result in actual for label in result["classifications"]}
        positive, predicted = fixture["failure"] is not None, bool(detected)
        key = (
            "true_positives"
            if positive and predicted
            else "false_negatives"
            if positive
            else "false_positives"
            if predicted
            else "true_negatives"
        )
        counts[key] += 1
        results.append(
            {
                "id": fixture["id"],
                "expected": fixture["failure"],
                "detected": sorted(detected),
                "passed": fixture["failure"] in detected if positive else not predicted,
            }
        )
    tp, fp, fn = counts["true_positives"], counts["false_positives"], counts["false_negatives"]
    return {
        "schema": "howldream.benchmark/v1",
        "suite": "dreambench",
        "fixtures": len(fixtures),
        **counts,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "results": results,
        "passed": all(r["passed"] for r in results),
        "elapsed_seconds": time.monotonic() - started,
        "limitations": (
            "14 authored grammar fixtures; not general hallucination detection performance."
        ),
    }
