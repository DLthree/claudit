"""CLI subcommand registration for the /harness skill."""

from __future__ import annotations

import argparse
from typing import Any


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the ``harness`` subcommand and its sub-actions."""
    harness = subparsers.add_parser(
        "harness", help="Extract code and analyze dependencies for test harnesses"
    )
    harness_sub = harness.add_subparsers(dest="action")

    # --- harness extract ---
    extract = harness_sub.add_parser(
        "extract", help="Extract functions or files verbatim"
    )
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

    # --- harness list-functions ---
    list_funcs = harness_sub.add_parser(
        "list-functions", help="List all functions in a file"
    )
    list_funcs.add_argument("project_dir", help="Path to the project")
    list_funcs.add_argument("--file", required=True, help="File to list functions from")

    # --- harness analyze-deps ---
    analyze = harness_sub.add_parser(
        "analyze-deps", help="Analyze function dependencies"
    )
    analyze.add_argument("project_dir", help="Path to the project")
    analyze.add_argument(
        "--functions",
        required=True,
        help="Comma-separated list of function names to analyze",
    )
    analyze.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Dependency depth (default: 1)",
    )

    # --- harness get-signature ---
    get_sig = harness_sub.add_parser(
        "get-signature", help="Get function signature"
    )
    get_sig.add_argument("project_dir", help="Path to the project")
    get_sig.add_argument("--function", required=True, help="Function name")
    get_sig.add_argument(
        "--language",
        choices=["c", "java", "python"],
        default=None,
        help="Language hint (auto-detected if omitted)",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Dispatch to the appropriate harness action."""
    from claudit.skills.harness import (
        extract_functions,
        extract_file,
        list_functions_in_file,
        analyze_dependencies,
        get_function_signature,
    )

    if args.action == "extract":
        if args.functions:
            function_list = [f.strip() for f in args.functions.split(",")]
            result = extract_functions(
                args.project_dir,
                function_list,
                language=args.language,
            )
        else:  # args.file
            result = extract_file(
                args.project_dir,
                args.file,
                language=args.language,
            )

        # Format for output
        return {
            "extracted": [
                {
                    "function": func.name,
                    "file": func.file,
                    "start_line": func.start_line,
                    "end_line": func.end_line,
                    "source": func.source,
                    "signature": func.signature,
                    "language": func.language,
                }
                for func in result
            ]
        }

    elif args.action == "list-functions":
        funcs = list_functions_in_file(args.project_dir, args.file)
        return {"functions": funcs, "count": len(funcs)}

    elif args.action == "analyze-deps":
        function_list = [f.strip() for f in args.functions.split(",")]
        deps = analyze_dependencies(
            args.project_dir,
            function_list,
            depth=args.depth,
        )
        return {
            "stub_functions": sorted(deps.stub_functions),
            "dependency_map": deps.dependency_map,
            "excluded_stdlib": sorted(deps.excluded_stdlib),
            "excluded_extracted": sorted(deps.excluded_extracted),
        }

    elif args.action == "get-signature":
        sig = get_function_signature(
            args.project_dir,
            args.function,
            language=args.language,
        )
        if sig is None:
            return {"error": f"Function '{args.function}' not found"}

        return {
            "name": sig.name,
            "return_type": sig.return_type,
            "parameters": [{"name": p.name, "type": p.type} for p in sig.parameters],
            "full_signature": sig.full_signature,
            "is_method": sig.is_method,
            "class_name": sig.class_name,
        }

    return {"error": f"Unknown harness action: {args.action}"}
