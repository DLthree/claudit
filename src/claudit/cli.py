"""CLI entry point for claudit skills."""

from __future__ import annotations

import argparse
import json
import sys

from claudit.skills.reachability import find_reachability


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="claudit",
        description="Code auditing skills for Claude Code",
    )
    sub = parser.add_subparsers(dest="command")

    # --- Register skill subcommands ---
    from claudit.skills.index.cli import register as register_index
    from claudit.skills.graph.cli import register as register_graph
    from claudit.skills.path.cli import register as register_path
    from claudit.skills.highlight.cli import register as register_highlight

    register_index(sub)
    register_graph(sub)
    register_path(sub)
    register_highlight(sub)

    # --- Legacy reachability sub-command (backward compat) ---
    reach = sub.add_parser(
        "reachability",
        help="Find call paths between two functions (legacy)",
    )
    reach.add_argument("source", help="Source function name")
    reach.add_argument("target", help="Target function name")
    reach.add_argument("project_dir", help="Path to the project to analyze")
    reach.add_argument(
        "--language",
        choices=["c", "java", "python"],
        default=None,
        help="Language hint (auto-detected if omitted)",
    )
    reach.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Maximum call-chain depth (default: 10)",
    )
    reach.add_argument(
        "--overrides",
        default=None,
        help="Path to manual overrides JSON file",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    # --- Dispatch ---
    if args.command == "reachability":
        result = find_reachability(
            source=args.source,
            target=args.target,
            project_dir=args.project_dir,
            language=args.language,
            max_depth=args.max_depth,
            overrides_path=args.overrides,
        )
        json.dump(result, sys.stdout, indent=2)
        print()
        return 0

    # Skill subcommands with two-level dispatch
    skill_dispatch = {
        "index": "claudit.skills.index.cli",
        "graph": "claudit.skills.graph.cli",
        "path": "claudit.skills.path.cli",
        "highlight": "claudit.skills.highlight.cli",
    }

    if args.command in skill_dispatch:
        # Check if action was provided
        if not getattr(args, "action", None):
            # Re-parse to show skill-specific help
            parser.parse_args([args.command, "--help"])
            return 1

        import importlib
        cli_mod = importlib.import_module(skill_dispatch[args.command])
        result = cli_mod.run(args)
        json.dump(result, sys.stdout, indent=2)
        print()
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
