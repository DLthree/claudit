"""CLI subcommand registration for the /highlight skill."""

from __future__ import annotations

import argparse
from typing import Any


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the ``highlight`` subcommand and its sub-actions."""
    hl = subparsers.add_parser("highlight", help="Syntax-highlighted source with annotations")
    hl_sub = hl.add_subparsers(dest="action")

    # --- highlight path ---
    hp = hl_sub.add_parser("path", help="Highlight all functions along a call path")
    hp.add_argument("functions", nargs="+", help="Function names forming the path")
    hp.add_argument("--project-dir", required=True, help="Path to the project")
    hp.add_argument(
        "--language",
        choices=["c", "java", "python"],
        default=None,
        help="Language hint (auto-detected if omitted)",
    )
    hp.add_argument(
        "--style",
        default="monokai",
        help="Pygments style name (default: monokai)",
    )

    # --- highlight function ---
    hf = hl_sub.add_parser("function", help="Highlight a single function")
    hf.add_argument("function", help="Function name")
    hf.add_argument("--project-dir", required=True, help="Path to the project")
    hf.add_argument(
        "--language",
        choices=["c", "java", "python"],
        default=None,
        help="Language hint (auto-detected if omitted)",
    )
    hf.add_argument(
        "--style",
        default="monokai",
        help="Pygments style name (default: monokai)",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Dispatch to the appropriate highlight action."""
    from claudit.skills.highlight import highlight_path, highlight_function

    if args.action == "path":
        return highlight_path(
            args.project_dir,
            args.functions,
            language=args.language,
            style=args.style,
        )

    if args.action == "function":
        result = highlight_function(
            args.project_dir,
            args.function,
            language=args.language,
            style=args.style,
        )
        return result if result is not None else {"error": "Function not found"}

    return {"error": f"Unknown highlight action: {args.action}"}
