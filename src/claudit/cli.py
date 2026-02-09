"""CLI entry point for claudit skills."""

from __future__ import annotations

import argparse
import importlib
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="claudit",
        description="Code auditing skills for Claude Code",
    )
    sub = parser.add_subparsers(dest="command")

    from claudit.skills.index.cli import register as register_index
    from claudit.skills.graph.cli import register as register_graph
    from claudit.skills.path.cli import register as register_path
    from claudit.skills.highlight.cli import register as register_highlight
    from claudit.skills.harness.cli import register as register_harness

    register_index(sub)
    register_graph(sub)
    register_path(sub)
    register_highlight(sub)
    register_harness(sub)

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    skill_dispatch = {
        "index": "claudit.skills.index.cli",
        "graph": "claudit.skills.graph.cli",
        "path": "claudit.skills.path.cli",
        "highlight": "claudit.skills.highlight.cli",
        "harness": "claudit.skills.harness.cli",
    }

    if args.command in skill_dispatch:
        if not getattr(args, "action", None):
            parser.parse_args([args.command, "--help"])
            return 1

        cli_mod = importlib.import_module(skill_dispatch[args.command])
        result = cli_mod.run(args)
        json.dump(result, sys.stdout, indent=2)
        print()
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
