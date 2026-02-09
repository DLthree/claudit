"""CLI subcommand registration for the /graph skill."""

from __future__ import annotations

import argparse
from typing import Any


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the ``graph`` subcommand and its sub-actions."""
    grp = subparsers.add_parser("graph", help="Call graph operations")
    grp_sub = grp.add_subparsers(dest="action")

    # --- graph build ---
    bld = grp_sub.add_parser("build", help="Build call graph")
    bld.add_argument("project_dir", help="Path to the project")
    bld.add_argument(
        "--language",
        choices=["c", "java", "python"],
        default=None,
        help="Language hint (auto-detected if omitted)",
    )
    bld.add_argument(
        "--overrides",
        default=None,
        help="Path to manual overrides JSON file",
    )
    bld.add_argument(
        "--force", action="store_true", help="Rebuild even if cached"
    )

    # --- graph show ---
    shw = grp_sub.add_parser("show", help="Dump full call graph")
    shw.add_argument("project_dir", help="Path to the project")
    shw.add_argument(
        "--no-auto-build",
        action="store_true",
        help="Fail if graph doesn't exist instead of auto-building",
    )

    # --- graph callees ---
    ce = grp_sub.add_parser("callees", help="List direct callees of a function")
    ce.add_argument("function", help="Function name")
    ce.add_argument("project_dir", help="Path to the project")
    ce.add_argument(
        "--no-auto-build",
        action="store_true",
        help="Fail if graph doesn't exist instead of auto-building",
    )

    # --- graph callers ---
    cr = grp_sub.add_parser("callers", help="List direct callers of a function")
    cr.add_argument("function", help="Function name")
    cr.add_argument("project_dir", help="Path to the project")
    cr.add_argument(
        "--no-auto-build",
        action="store_true",
        help="Fail if graph doesn't exist instead of auto-building",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Dispatch to the appropriate graph action."""
    from claudit.skills.graph import build, show, callees, callers

    if args.action == "build":
        return build(
            args.project_dir,
            language=args.language,
            overrides_path=args.overrides,
            force=args.force,
        )

    if args.action == "show":
        return show(args.project_dir, auto_build=not args.no_auto_build)

    if args.action == "callees":
        return callees(
            args.project_dir,
            args.function,
            auto_build=not args.no_auto_build,
        )

    if args.action == "callers":
        return callers(
            args.project_dir,
            args.function,
            auto_build=not args.no_auto_build,
        )

    return {"error": f"Unknown graph action: {args.action}"}
