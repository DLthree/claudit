"""CLI subcommand registration for the /index skill."""

from __future__ import annotations

import argparse
from typing import Any


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the ``index`` subcommand and its sub-actions."""
    idx = subparsers.add_parser("index", help="Manage GNU Global indexes")
    idx_sub = idx.add_subparsers(dest="action")

    # --- index create ---
    create = idx_sub.add_parser("create", help="Create or rebuild index")
    create.add_argument("project_dir", help="Path to the project")
    create.add_argument(
        "--force", action="store_true", help="Rebuild even if index exists"
    )

    # --- index list-symbols ---
    ls = idx_sub.add_parser("list-symbols", help="List all indexed symbols")
    ls.add_argument("project_dir", help="Path to the project")
    ls.add_argument(
        "--no-auto-index",
        action="store_true",
        help="Fail if index doesn't exist instead of auto-creating",
    )

    # --- index get-body ---
    gb = idx_sub.add_parser("get-body", help="Get function body source")
    gb.add_argument("function", help="Function name")
    gb.add_argument("project_dir", help="Path to the project")
    gb.add_argument(
        "--language",
        choices=["c", "java", "python"],
        default=None,
        help="Language hint (auto-detected if omitted)",
    )
    gb.add_argument(
        "--no-auto-index",
        action="store_true",
        help="Fail if index doesn't exist instead of auto-creating",
    )

    # --- index lookup ---
    lu = idx_sub.add_parser("lookup", help="Find definitions/references")
    lu.add_argument("symbol", help="Symbol name to look up")
    lu.add_argument("project_dir", help="Path to the project")
    lu.add_argument(
        "--kind",
        choices=["definitions", "references", "both"],
        default="both",
        help="What to look up (default: both)",
    )
    lu.add_argument(
        "--no-auto-index",
        action="store_true",
        help="Fail if index doesn't exist instead of auto-creating",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Dispatch to the appropriate index action."""
    from claudit.skills.index import create, list_symbols, get_body, lookup

    if args.action == "create":
        return create(args.project_dir, force=args.force)

    if args.action == "list-symbols":
        return list_symbols(
            args.project_dir,
            auto_index=not args.no_auto_index,
        )

    if args.action == "get-body":
        result = get_body(
            args.project_dir,
            args.function,
            language=args.language,
            auto_index=not args.no_auto_index,
        )
        return result if result is not None else {"error": "Function not found"}

    if args.action == "lookup":
        return lookup(
            args.project_dir,
            args.symbol,
            kind=args.kind,
            auto_index=not args.no_auto_index,
        )

    return {"error": f"Unknown index action: {args.action}"}
