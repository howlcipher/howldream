"""The howl.interop/v1 descriptor matches the real command line.

HowlPlane and ``howl doctor`` read ``howldream interop --json`` to check that
the commands and flags they run still exist, so the descriptor must describe
the parser exactly and name the documents callers rely on.
"""

import json
import re
import sys

from howldream import __version__
from howldream.cli import build_parser, main

FLAG = re.compile(r"^--?[A-Za-z0-9][A-Za-z0-9_-]*$")
SCHEMA_ID = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+/v[0-9]+$")


def descriptor(monkeypatch, capsys) -> dict:
    monkeypatch.setattr(sys, "argv", ["howldream", "interop", "--json"])
    assert main() == 0
    return json.loads(capsys.readouterr().out)


def test_descriptor_shape(monkeypatch, capsys):
    d = descriptor(monkeypatch, capsys)
    assert d["schema"] == "howl.interop/v1"
    assert d["component"] == "howldream"
    assert d["version"] == __version__
    assert set(d["exit_codes"]) == {"0", "1", "2"}
    for command in d["commands"]:
        assert isinstance(command["path"], list) and isinstance(command["json"], bool)
        assert all(FLAG.match(flag) for flag in command["flags"]), command
        for schema in command.get("emits", []) + command.get("accepts", []):
            assert SCHEMA_ID.match(schema), schema


def test_version_matches_pyproject():
    from pathlib import Path

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    assert __version__ == data["project"]["version"]


def test_every_subcommand_and_flag_is_described(monkeypatch, capsys):
    described = {
        tuple(c["path"]): set(c["flags"]) for c in descriptor(monkeypatch, capsys)["commands"]
    }
    parser = build_parser()
    subparsers = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction")
    for name, sub in subparsers.choices.items():
        flags = {o for a in sub._actions for o in a.option_strings} - {"-h", "--help"}
        assert described[(name,)] == flags, name
    assert "--version" in described[()]


def test_commands_howlplane_runs_are_described(monkeypatch, capsys):
    commands = {tuple(c["path"]): c for c in descriptor(monkeypatch, capsys)["commands"]}
    explore = commands[("explore",)]
    assert {"--output", "--from-candidate", "--command-config", "--allow-remote"} <= set(
        explore["flags"]
    )
    assert "howl.exploration_result/v1" in explore["emits"]
    assert {"--candidate-id", "--format"} <= set(commands[("export",)]["flags"])
    assert "howl.candidate/v1" in commands[("export",)]["emits"]
    assert {"--external", "--out", "--rank"} <= set(commands[("cluster",)]["flags"])
    assert commands[("report",)]["json"] is False


def test_evaluate_accepts_the_unblinding_map_it_already_supported():
    args = build_parser().parse_args(["evaluate", "dreamvalue", "--unblind", "map.json"])
    assert str(args.unblind) == "map.json"
