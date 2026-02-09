"""CLI subcommand registration for the /harness skill."""

from __future__ import annotations

import argparse
from typing import Any


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the ``harness`` subcommand and its sub-actions."""
    harness = subparsers.add_parser(
        "harness", help="Generate test harnesses from extracted functions"
    )
    harness_sub = harness.add_subparsers(dest="action")

    # --- harness extract ---
    extract = harness_sub.add_parser(
        "extract", help="Extract functions and generate harness with stubs"
    )

    # Mutually exclusive: either --functions or --file
    target = extract.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--functions",
        help="Comma-separated list of function names to extract",
    )
    target.add_argument(
        "--file",
        help="Extract all functions from this file (relative path)",
    )

    extract.add_argument("project_dir", help="Path to the project")

    extract.add_argument(
        "--language",
        choices=["c", "java", "python"],
        default=None,
        help="Language hint (auto-detected if omitted)",
    )

    extract.add_argument(
        "--include-main",
        action="store_true",
        help="Generate a main() function for testing",
    )

    extract.add_argument(
        "--stub-depth",
        type=int,
        default=1,
        help="How many dependency levels to stub (default: 1)",
    )

    extract.add_argument(
        "--no-auto-index",
        action="store_true",
        help="Don't auto-create index and call graph",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Dispatch to the appropriate harness action."""
    from claudit.skills.harness import extract_functions, extract_file

    if args.action == "extract":
        auto_index = not args.no_auto_index

        if args.functions:
            # Extract specific functions
            function_list = [f.strip() for f in args.functions.split(",")]

            return extract_functions(
                args.project_dir,
                function_list,
                language=args.language,
                include_main=args.include_main,
                stub_depth=args.stub_depth,
                auto_index=auto_index,
            )

        elif args.file:
            # Extract all functions from file
            return extract_file(
                args.project_dir,
                args.file,
                language=args.language,
                include_main=args.include_main,
                stub_depth=args.stub_depth,
                auto_index=auto_index,
            )

    return {"error": f"Unknown harness action: {args.action}"}
