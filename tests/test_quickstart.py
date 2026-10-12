"""Exercise the literal README exploration command through the installed CLI."""

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


def test_readme_quickstart_exploration_is_offline_and_bounded(tmp_path):
    root = Path(__file__).resolve().parents[1]
    quickstart = (root / "README.md").read_text().split("## Quick start\n", 1)[1]
    commands = quickstart.split("```bash\n", 1)[1].split("```", 1)[0]
    command = next(
        line
        for line in commands.replace("\\\n", " ").splitlines()
        if line.startswith("howldream explore ")
    )
    shutil.copytree(root / "examples", tmp_path / "examples")
    executable = Path(sys.executable).parent / "howldream"
    env = {**os.environ, "HOWL_FORBID_LOCAL_INFERENCE": "1"}
    result = subprocess.run(
        [str(executable), *shlex.split(command)[1:]],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    run_dirs = list((tmp_path / ".howldream/runs").iterdir())
    assert len(run_dirs) == 1
    manifest = json.loads((run_dirs[0] / "manifest.json").read_text())
    assert manifest["status"] == "COMPLETE"
    assert manifest["call_count"] == 3
    candidates = [
        json.loads(line) for line in (run_dirs[0] / "candidates.jsonl").read_text().splitlines()
    ]
    baseline = [
        json.loads(line) for line in (run_dirs[0] / "baseline.jsonl").read_text().splitlines()
    ]
    assert len(candidates) == 2
    assert len(baseline) == 1
    for candidate in baseline + candidates:
        execution = candidate["execution"]
        assert execution["mocked"] is True
        assert execution["inference_occurred"] is False
        assert execution["remote"] is False
