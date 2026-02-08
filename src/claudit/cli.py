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

    # --- reachability sub-command ---
    reach = sub.add_parser(
        "reachability",
        help="Find call paths between two functions",
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

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
