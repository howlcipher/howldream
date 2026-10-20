"""The ``howl.interop/v1`` descriptor printed by ``howldream interop --json``.

Other Howl components run HowlDream through its command line (HowlPlane runs
``explore``, ``export`` and ``cluster``). The descriptor states which commands
and flags exist, which JSON documents each prints or writes, and what the exit
codes mean, so ``howl doctor`` can check a caller against the installed
release. It is built from the live argparse tree, so it cannot list a flag the
CLI does not accept. Contract:
https://github.com/howlcipher/howl/blob/main/docs/INTEROP.md
"""

import argparse

from howldream import __version__

SCHEMA = "howl.interop/v1"

EXIT_CODES = {
    "0": "ok",
    "1": "completed with a negative outcome: a PARTIAL run or exploration, "
    "audit-report findings, or a failed benchmark",
    "2": "error or invalid input; a JSON object with an `error` key is printed on stderr",
}

ENV = ["HOWLDREAM_API_KEY", "HOWL_FORBID_LOCAL_INFERENCE"]

# Every command prints JSON on stdout except `report`, which prints Markdown.
NOT_JSON = {"report"}

EMITS = {
    "explore": ["howl.exploration_result/v1", "howl.exploration/v1"],
    "export": ["howl.candidate/v1"],
    "review": ["howl.assessment/v1"],
    "cluster": ["howldream.external_discovery/v1"],
    "run": ["howldream.run/v1", "howldream.handoff/v1"],
    "dream": ["howldream.run/v1", "howldream.handoff/v1"],
    "nightmare": ["howldream.run/v1", "howldream.handoff/v1"],
    "interop": [SCHEMA],
}

ACCEPTS = {
    "explore": ["howl.exploration/v1", "howl.candidate/v1"],
    "review": ["howl.candidate/v1"],
}


def _flags(parser: argparse.ArgumentParser) -> list[str]:
    return sorted(
        option
        for action in parser._actions
        for option in action.option_strings
        if option not in ("-h", "--help")
    )


def describe(parser: argparse.ArgumentParser) -> dict:
    """Return the descriptor for ``parser`` and its subcommands."""
    commands: list[dict] = []

    def walk(current: argparse.ArgumentParser, path: list[str]) -> None:
        name = path[-1] if path else ""
        entry: dict = {
            "path": path,
            "flags": _flags(current),
            "json": bool(path) and name not in NOT_JSON,
        }
        if name in EMITS:
            entry["emits"] = EMITS[name]
        if name in ACCEPTS:
            entry["accepts"] = ACCEPTS[name]
        commands.append(entry)
        for action in current._actions:
            if isinstance(action, argparse._SubParsersAction):
                for sub_name, sub in action.choices.items():
                    walk(sub, [*path, sub_name])

    walk(parser, [])
    return {
        "schema": SCHEMA,
        "component": "howldream",
        "version": __version__,
        "commands": commands,
        "exit_codes": EXIT_CODES,
        "env": ENV,
        "consumes": [],
    }
