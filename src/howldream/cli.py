"""CLI with JSON results and actionable errors, without secret-bearing traces."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError
from yaml import YAMLError

from howldream import __version__
from howldream.artifacts import load_run, scrub
from howldream.benchmark import benchmark
from howldream.engine import replay, run, wake
from howldream.schema import read_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description="HowlDream: dream output is data, not authority.")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run", "dream", "nightmare", "wake", "replay", "inspect", "report"):
        sub = commands.add_parser(name)
        sub.add_argument("target", type=Path)
        if name == "replay":
            sub.add_argument(
                "--allow-remote",
                action="store_true",
                help="allow the reviewed stored endpoint to receive this replay",
            )
        sub.add_argument(
            "--output", type=Path, default=Path(".howldream/runs"), help="artifact storage root"
        )
    commands.add_parser("benchmark").add_argument(
        "suite", nargs="?", choices=["dreambench"], default="dreambench"
    )
    commands.add_parser("compare").add_argument("targets", type=Path, nargs="+")
    args = parser.parse_args()
    result: dict | list
    try:
        if args.command == "benchmark":
            result = benchmark()
            print(json.dumps(result, indent=2))
            return 0 if result["passed"] else 1
        if args.command == "compare":
            result = [{"run_id": p.name, "metrics": load_run(p)["metrics"]} for p in args.targets]
        elif args.command in {"inspect", "report"}:
            artifacts = load_run(args.target)
            if args.command == "report":
                print((args.target / "report.md").read_text())
                return 0
            result = artifacts
        else:
            if args.command in {"wake", "replay"}:
                path = (
                    replay(args.target, args.output, args.allow_remote)
                    if args.command == "replay"
                    else wake(args.target, args.output)
                )
            else:
                experiment = read_experiment(args.target)
                if args.command == "validate":
                    print(json.dumps({"valid": True, "name": experiment.name}))
                    return 0
                if args.command in {"dream", "nightmare"}:
                    experiment.mode = args.command
                path = run(experiment, args.output, wake_now=args.command == "run")
            artifacts = load_run(path)
            result = {
                "run_id": path.name,
                "path": str(path.resolve()),
                "status": artifacts["manifest"]["status"],
            }
            print(json.dumps(result))
            return 1 if result["status"] == "PARTIAL" else 0
        print(json.dumps(scrub(result), indent=2))
        return 0
    except ValidationError as error:
        details = [
            {"field": ".".join(map(str, e["loc"])), "problem": e["type"]} for e in error.errors()
        ]
        print(json.dumps({"error": "invalid experiment", "details": details}), file=sys.stderr)
    except (OSError, YAMLError, ValueError, KeyError, TypeError) as error:
        message = (
            str(error)
            if isinstance(error, ValueError)
            else "Cannot read input; check file paths, schema, and permissions."
        )
        print(json.dumps({"error": scrub(message)}), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
