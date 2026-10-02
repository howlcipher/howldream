"""CLI with JSON results and actionable errors, without secret-bearing traces."""

import argparse
import json
import sys
from pathlib import Path

import yaml
from howl_provider_core import CommandConfig
from pydantic import ValidationError
from yaml import YAMLError

from howldream import __version__
from howldream.artifacts import load_run, scrub
from howldream.benchmark import benchmark, list_benchmarks
from howldream.contracts import CandidateHandoff, DescentDAG, ExplorationRequest
from howldream.dreamvalue import evaluate
from howldream.engine import explore, replay, run, wake
from howldream.interop import exploration_from_candidate, export_candidate, review_candidate
from howldream.providers import RemoteCommandProvider
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
    explore_parser.add_argument(
        "target", type=Path, nargs="?", help="exploration request file (JSON or YAML)"
    )
    explore_parser.add_argument(
        "--output", type=Path, default=Path(".howldream/runs"), help="artifact storage root"
    )

    explore_parser.add_argument("--from-candidate", type=Path)
    explore_parser.add_argument("--objective")
    explore_parser.add_argument("--evidence", type=Path)
    claim_audit = commands.add_parser("audit-report")
    claim_audit.add_argument("target", type=Path)
    claim_audit.add_argument("--validation", type=Path, required=True)
    audit_parser = commands.add_parser("audit-attribution")
    audit_parser.add_argument("target", type=Path, help="Chronology ledger JSON")
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

    export_parser = commands.add_parser("export")
    export_parser.add_argument("target", type=Path)
    export_parser.add_argument("--candidate-id", required=True)
    export_parser.add_argument(
        "--format", choices=["howl.candidate/v1"], default="howl.candidate/v1"
    )
    review_parser = commands.add_parser("review")
    review_parser.add_argument("target", type=Path)
    review_parser.add_argument("--evidence", type=Path)
    for name in ("run", "dream", "nightmare", "explore"):
        commands.choices[name].add_argument("--max-calls", type=int)
        commands.choices[name].add_argument("--command-config", type=Path)
        commands.choices[name].add_argument("--allow-remote", action="store_true")
    args = parser.parse_args()
    result: dict | list
    try:
        provider_override = None
        if getattr(args, "command_config", None):
            if not args.allow_remote:
                raise ValueError("command requires --allow-remote after reviewing the profile")
            provider_override = RemoteCommandProvider(CommandConfig.read(args.command_config))
        if args.command == "validate":
            from howldream.validation import validate_artifact

            print(json.dumps(validate_artifact(args.target)))
            return 0
        if args.command == "audit-report":
            from howldream.evidence import ReportEvidence, audit_report

            ledger = ReportEvidence.model_validate(json.loads(args.validation.read_text()))
            result = audit_report(args.target.read_text(), ledger)
            print(json.dumps(scrub(result), indent=2))
            return 1 if result["findings"] else 0
        if args.command == "audit-attribution":
            from howldream.attribution import audit_attribution

            audit_result = audit_attribution(json.loads(args.target.read_text()))
            print(json.dumps(audit_result, indent=2))
            return 1 if audit_result["conflicts"] or audit_result["unresolved"] else 0
        if args.command == "export":
            print(export_candidate(args.target, args.candidate_id).model_dump_json(indent=2))
            return 0
        if args.command == "review":
            from howldream.schema import Evidence

            candidate = CandidateHandoff.model_validate(json.loads(args.target.read_text()))
            evidence = (
                [Evidence.model_validate(x) for x in json.loads(args.evidence.read_text())]
                if args.evidence
                else []
            )
            print(review_candidate(candidate, evidence).model_dump_json(indent=2))
            return 0
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
            if bool(args.target) == bool(args.from_candidate):
                raise ValueError("explore requires one request path or --from-candidate")
            if args.from_candidate:
                from howldream.schema import Evidence

                candidate = CandidateHandoff.model_validate(
                    json.loads(args.from_candidate.read_text())
                )
                evidence = (
                    [Evidence.model_validate(x) for x in json.loads(args.evidence.read_text())]
                    if args.evidence
                    else []
                )
                req = exploration_from_candidate(
                    candidate,
                    objective=args.objective,
                    evidence=evidence,
                    remote=bool(provider_override),
                    max_calls=args.max_calls if args.max_calls is not None else 3,
                )
            else:
                req = ExplorationRequest.model_validate(yaml.safe_load(args.target.read_text()))
            if args.max_calls is not None:
                req.budget.max_calls = args.max_calls
                req = ExplorationRequest.model_validate(req.model_dump())
            if provider_override:
                if req.budget.local_only or "command" not in req.budget.provider_allowlist:
                    raise ValueError(
                        "command requires remote budget permission and command allowlist"
                    )
                req.provider = {
                    "kind": "command",
                    "allow_remote": True,
                    "model": getattr(provider_override.adapter.config, "model", None) or "command",
                }
            _run_dir, exp_res = explore(req, args.output, provider_override=provider_override)
            print(exp_res.model_dump_json(indent=2))
            return 1 if load_run(_run_dir)["manifest"]["status"] == "PARTIAL" else 0
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
                if args.max_calls is not None:
                    experiment.max_calls = args.max_calls
                    experiment = type(experiment).model_validate(experiment.model_dump())
                if provider_override:
                    experiment.provider.kind = "command"
                    experiment.provider.allow_remote = True
                    experiment.provider.model = (
                        getattr(provider_override.adapter.config, "model", None) or "command"
                    )
                path = run(
                    experiment,
                    args.output,
                    wake_now=args.command == "run",
                    provider_override=provider_override,
                )
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
