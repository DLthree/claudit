"""CLI subcommand registration for the /path skill."""

from __future__ import annotations

import argparse
from typing import Any


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the ``path`` subcommand and its sub-actions."""
    pth = subparsers.add_parser("path", help="Call path operations")
    pth_sub = pth.add_subparsers(dest="action")

    # --- path find ---
    fnd = pth_sub.add_parser("find", help="Find call paths between functions")
    fnd.add_argument("source", help="Source function name")
    fnd.add_argument("target", help="Target function name")
    fnd.add_argument("project_dir", help="Path to the project")
    fnd.add_argument(
        "--language",
        choices=["c", "java", "python"],
        default=None,
        help="Language hint (auto-detected if omitted)",
    )
    fnd.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Maximum call-chain depth (default: 10)",
    )
    fnd.add_argument(
        "--overrides",
        default=None,
        help="Path to manual overrides JSON file",
    )
    fnd.add_argument(
        "--no-annotate",
        action="store_true",
        help="Skip annotation (return function names only)",
    )
    fnd.add_argument(
        "--no-auto-build",
        action="store_true",
        help="Fail if graph doesn't exist instead of auto-building",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Dispatch to the appropriate path action."""
    from claudit.skills.path import find

    if args.action == "find":
        return find(
            args.project_dir,
            args.source,
            args.target,
            max_depth=args.max_depth,
            annotate=not args.no_annotate,
            auto_build=not args.no_auto_build,
            language=args.language,
            overrides_path=args.overrides,
        )

    return {"error": f"Unknown path action: {args.action}"}
