"""Run Milestone 3.1 self-dogfood audit challenging published Milestone Three claims."""

from pathlib import Path

from howldream.engine import run, wake
from howldream.schema import read_experiment


def main():
    root = Path("dogfood/milestone_three")
    root.mkdir(parents=True, exist_ok=True)
    yaml_path = Path("examples/milestone_three_audit_dogfood.yaml")
    experiment = read_experiment(yaml_path)

    print(
        f"Running Milestone 3.1 audit experiment '{experiment.name}' on {experiment.provider.model}..."
    )
    run_path = run(experiment, root, wake_now=False)
    print(f"Audit run complete: {run_path.name}")

    print("Running WAKE analysis descendant...")
    wake_path = wake(run_path, root)
    print(f"WAKE descendant complete: {wake_path.name}")

    report_text = (wake_path / "report.md").read_text()
    print("\n--- AUDIT WAKE REPORT SUMMARY ---")
    print(report_text[:1200])


if __name__ == "__main__":
    main()
