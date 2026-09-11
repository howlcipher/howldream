"""CLI with JSON results and actionable errors, without secret-bearing traces."""

import argparse
import json
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError
from yaml import YAMLError

from howldream import __version__
from howldream.artifacts import load_run, scrub
from howldream.benchmark import benchmark, list_benchmarks
from howldream.contracts import DescentDAG, ExplorationRequest
from howldream.dreamvalue import evaluate
from howldream.engine import explore, replay, run, wake
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
    benchmark_parser = commands.add_parser("benchmark")
    benchmark_parser.add_argument(
        "action", nargs="?", choices=["list", "run", "report", "dreambench"]
    )
    benchmark_parser.add_argument("suite_or_run", nargs="?", type=Path)
    benchmark_parser.add_argument(
        "--split",
        choices=["development", "validation", "held_out", "confirmation", "all"],
        default="development",
    )
    benchmark_parser.add_argument(
        "--benchmark-version",
        choices=["0.2.0", "0.3.0"],
        default="0.2.0",
        help="benchmark dataset version to evaluate",
    )
    benchmark_parser.add_argument("--output", type=Path, default=Path(".howldream/benchmarks"))
    evaluate_parser = commands.add_parser("evaluate")
    evaluate_parser.add_argument("suite", choices=["dreamvalue"])
    evaluate_parser.add_argument("--input", type=Path)
    evaluate_parser.add_argument("--output", type=Path, default=Path(".howldream/evaluations"))
    evaluate_parser.add_argument("--reviews", type=Path, help="annotated human review path")
    commands.add_parser("compare").add_argument("targets", type=Path, nargs="+")

    explore_parser = commands.add_parser("explore")
    explore_parser.add_argument("target", type=Path, help="exploration request file (JSON or YAML)")
    explore_parser.add_argument(
        "--output", type=Path, default=Path(".howldream/runs"), help="artifact storage root"
    )

    trace_parser = commands.add_parser("trace")
    trace_parser.add_argument("target_id", help="node or candidate ID to trace backwards")
    trace_parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="run directory containing exploration_envelope.json",
    )
    trace_parser.add_argument(
        "--output", type=Path, default=Path(".howldream/runs"), help="runs root directory"
    )

    args = parser.parse_args()
    result: dict | list
    try:
        if args.command == "benchmark":
            if args.action == "list":
                result = list_benchmarks()
                print(json.dumps(result, indent=2))
                return 0
            if args.action == "report":
                if args.suite_or_run is None:
                    raise ValueError("benchmark report requires a result path")
                result = json.loads(args.suite_or_run.read_text())
                print(json.dumps(result, indent=2))
                return 0
            if args.action == "run" and (
                args.suite_or_run is None or args.suite_or_run.name != "dreambench"
            ):
                raise ValueError("benchmark run requires suite dreambench")
            result = benchmark(split=args.split, output=args.output, version=args.benchmark_version)
            print(json.dumps(result, indent=2))
            return 0 if result["passed"] else 1
        if args.command == "evaluate":
            result = evaluate(
                args.input,
                args.output,
                reviews_path=getattr(args, "reviews", None),
                unblinding_path=getattr(args, "unblind", None),
            )
            print(json.dumps(result, indent=2))
            return 0
        if args.command == "explore":
            raw_content = args.target.read_text()
            data = yaml.safe_load(raw_content)
            req = ExplorationRequest.model_validate(data)
            _run_dir, exp_res = explore(req, args.output)
            print(exp_res.model_dump_json(indent=2))
            return 0
        if args.command == "trace":
            target_run_dir = args.run_dir
            if target_run_dir is None and args.output.exists():
                cand_id = args.target_id
                prefix = cand_id.split("/")[0]
                possible = args.output / prefix
                if possible.is_dir() and (possible / "exploration_envelope.json").exists():
                    target_run_dir = possible
                else:
                    for p in sorted(args.output.iterdir(), reverse=True):
                        if p.is_dir() and (p / "exploration_envelope.json").exists():
                            target_run_dir = p
                            break
            if (
                target_run_dir is None
                or not (target_run_dir / "exploration_envelope.json").exists()
            ):
                raise ValueError(f"cannot find exploration envelope for target '{args.target_id}'")
            env_data = json.loads((target_run_dir / "exploration_envelope.json").read_text())
            dag = DescentDAG.model_validate(env_data["descent_dag"])
            chain = dag.trace(args.target_id)
            print(json.dumps([n.model_dump() for n in chain], indent=2))
            return 0
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
