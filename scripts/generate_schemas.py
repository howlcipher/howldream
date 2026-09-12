#!/usr/bin/env python3
"""Generate canonical JSON Schema for the versioned howl.* ecosystem envelopes.

`src/howldream/contracts.py` is the sole authoritative source. These schemas
are generated, never hand-edited — see schemas/README.md for the evolution
policy and vendoring architecture. Run with `--check` in CI to fail the build
if contracts.py changed without regenerating schemas/ (drift detection).
"""

from __future__ import annotations

import argparse
import filecmp
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from howldream.contracts import (
    CandidateAssessment,
    CandidateHandoff,
    DevelopmentResult,
    ExplorationRequest,
    ExplorationResult,
)

REPO_RAW_BASE = "https://raw.githubusercontent.com/howlcipher/howldream/main/schemas"

# (schema family slug, model class, human title) — one entry per versioned
# howl.* envelope. This is the complete, currently-known public contract
# surface: every model in contracts.py carrying a `schema_version: Literal[...]`
# field. Re-verify this list against contracts.py whenever a new envelope is
# added; do not assume it is exhaustive without checking.
ENVELOPES: list[tuple[str, type[Any], str]] = [
    (
        "howl.exploration.v1",
        ExplorationRequest,
        "HowlDream Exploration Request (howl.exploration/v1)",
    ),
    ("howl.candidate.v1", CandidateHandoff, "HowlDream Candidate Handoff (howl.candidate/v1)"),
    (
        "howl.assessment.v1",
        CandidateAssessment,
        "HowlFrame Candidate Assessment (howl.assessment/v1)",
    ),
    (
        "howl.development_result.v1",
        DevelopmentResult,
        "HowlCreate Development Result (howl.development_result/v1)",
    ),
    (
        "howl.exploration_result.v1",
        ExplorationResult,
        "HowlDream Exploration Result (howl.exploration_result/v1)",
    ),
]


def build_schema(slug: str, model: type[Any], title: str) -> dict[str, Any]:
    schema = model.model_json_schema(mode="validation")
    schema = {
        **schema,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{REPO_RAW_BASE}/{slug}.schema.json",
        "title": title,
    }
    return schema


def write_schemas(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for slug, model, title in ENVELOPES:
        schema = build_schema(slug, model, title)
        path = out_dir / f"{slug}.schema.json"
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate into a temp dir and fail if schemas/ has drifted from contracts.py",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    schemas_dir = repo_root / "schemas"

    if not args.check:
        written = write_schemas(schemas_dir)
        for path in written:
            print(f"wrote {path.relative_to(repo_root)}")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        write_schemas(tmp_dir)
        drift = False
        for slug, _model, _title in ENVELOPES:
            name = f"{slug}.schema.json"
            checked_in = schemas_dir / name
            regenerated = tmp_dir / name
            if not checked_in.exists():
                print(f"DRIFT: {name} does not exist in schemas/ (run without --check)")
                drift = True
                continue
            if not filecmp.cmp(checked_in, regenerated, shallow=False):
                print(
                    f"DRIFT: {name} does not match contracts.py (run without --check to regenerate)"
                )
                drift = True
        if drift:
            return 1
        print(f"schemas/ matches contracts.py for all {len(ENVELOPES)} envelopes")
        return 0


if __name__ == "__main__":
    sys.exit(main())
