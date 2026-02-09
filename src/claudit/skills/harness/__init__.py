"""Test harness generation skill.

Public API
----------
- extract_functions(project_dir, function_names, *, language=None,
                   include_main=False, stub_depth=1, auto_index=True) -> dict
- extract_file(project_dir, filepath, *, language=None,
              include_main=False, stub_depth=1, auto_index=True) -> dict
"""

from __future__ import annotations

from typing import Any

from claudit.lang import detect_language
from claudit.skills.index.indexer import ensure_index
from claudit.skills.graph import build as build_graph
from claudit.skills.graph.cache import load_call_graph
from claudit.skills.harness.extractor import (
    extract_target_functions,
    extract_functions_from_file,
)
from claudit.skills.harness.dependency_analyzer import (
    analyze_dependencies,
    filter_stub_functions,
)
from claudit.skills.harness.stubber import generate_stubs
from claudit.skills.harness.assembler import assemble_harness, extract_includes


def extract_functions(
    project_dir: str,
    function_names: list[str],
    *,
    language: str | None = None,
    include_main: bool = False,
    stub_depth: int = 1,
    auto_index: bool = True,
) -> dict[str, Any]:
    """Extract specific functions and generate test harness.

    Args:
        project_dir: Project directory path
        function_names: List of function names to extract
        language: Target language (c, java, python) - auto-detected if None
        include_main: Generate a main() function for testing
        stub_depth: How many levels deep to analyze dependencies (default: 1)
        auto_index: Auto-create index and call graph if needed

    Returns:
        Dict with keys:
        - extracted: List of extracted function info
        - stubs: List of stub function info
        - includes: List of include/import statements
        - complete_harness: Full assembled harness source code
        - language: Detected/specified language
        - stats: Statistics (counts, lines)

    Raises:
        ValueError: If a function cannot be found
    """
    # Detect language if not specified
    if language is None:
        language = detect_language(project_dir)

    # Ensure index exists
    if auto_index:
        ensure_index(project_dir)

    # Extract target functions (verbatim!)
    extracted = extract_target_functions(project_dir, function_names, language)

    # Build call graph if needed
    call_graph = _ensure_call_graph(project_dir, language, auto_index)

    # Analyze dependencies
    extracted_names = {func.name for func in extracted}
    dep_set = analyze_dependencies(
        project_dir,
        extracted_names,
        call_graph,
        stub_depth=stub_depth,
    )

    # Filter stub functions to ensure they exist in project
    filtered_stubs = filter_stub_functions(dep_set.stub_functions, project_dir)

    # Generate stubs
    stubs = generate_stubs(
        project_dir,
        filtered_stubs,
        language,
        dep_set.dependency_map,
    )

    # Extract includes
    includes = extract_includes(project_dir, extracted, language)

    # Assemble complete harness
    complete_harness = assemble_harness(
        project_dir,
        extracted,
        stubs,
        language,
        include_main=include_main,
    )

    # Calculate stats
    total_lines = complete_harness.count("\n") + 1

    return {
        "extracted": [
            {
                "function": func.name,
                "file": func.file,
                "start_line": func.start_line,
                "end_line": func.end_line,
                "source": func.source,
                "signature": func.signature,
            }
            for func in extracted
        ],
        "stubs": [
            {
                "function": stub.name,
                "signature": stub.signature,
                "stub_source": stub.stub_source,
                "return_type": stub.return_type,
                "reason": stub.reason,
                "original_file": stub.original_file,
            }
            for stub in stubs
        ],
        "includes": includes,
        "complete_harness": complete_harness,
        "language": language,
        "stats": {
            "extracted_count": len(extracted),
            "stub_count": len(stubs),
            "total_lines": total_lines,
        },
    }


def extract_file(
    project_dir: str,
    filepath: str,
    *,
    language: str | None = None,
    include_main: bool = False,
    stub_depth: int = 1,
    auto_index: bool = True,
) -> dict[str, Any]:
    """Extract all functions from a file and generate test harness.

    Args:
        project_dir: Project directory path
        filepath: Relative path to source file from project root
        language: Target language (c, java, python) - auto-detected if None
        include_main: Generate a main() function for testing
        stub_depth: How many levels deep to analyze dependencies (default: 1)
        auto_index: Auto-create index and call graph if needed

    Returns:
        Same format as extract_functions()

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    # Detect language if not specified
    if language is None:
        language = detect_language(project_dir)

    # Ensure index exists
    if auto_index:
        ensure_index(project_dir)

    # Extract all functions from file
    extracted = extract_functions_from_file(project_dir, filepath, language)

    if not extracted:
        # No functions found in file
        return {
            "extracted": [],
            "stubs": [],
            "includes": [],
            "complete_harness": _generate_empty_harness(language),
            "language": language,
            "stats": {
                "extracted_count": 0,
                "stub_count": 0,
                "total_lines": 0,
            },
        }

    # Build call graph if needed
    call_graph = _ensure_call_graph(project_dir, language, auto_index)

    # Analyze dependencies
    extracted_names = {func.name for func in extracted}
    dep_set = analyze_dependencies(
        project_dir,
        extracted_names,
        call_graph,
        stub_depth=stub_depth,
    )

    # Filter and generate stubs
    filtered_stubs = filter_stub_functions(dep_set.stub_functions, project_dir)
    stubs = generate_stubs(
        project_dir,
        filtered_stubs,
        language,
        dep_set.dependency_map,
    )

    # Extract includes
    includes = extract_includes(project_dir, extracted, language)

    # Assemble complete harness
    complete_harness = assemble_harness(
        project_dir,
        extracted,
        stubs,
        language,
        include_main=include_main,
    )

    # Calculate stats
    total_lines = complete_harness.count("\n") + 1

    return {
        "extracted": [
            {
                "function": func.name,
                "file": func.file,
                "start_line": func.start_line,
                "end_line": func.end_line,
                "source": func.source,
                "signature": func.signature,
            }
            for func in extracted
        ],
        "stubs": [
            {
                "function": stub.name,
                "signature": stub.signature,
                "stub_source": stub.stub_source,
                "return_type": stub.return_type,
                "reason": stub.reason,
                "original_file": stub.original_file,
            }
            for stub in stubs
        ],
        "includes": includes,
        "complete_harness": complete_harness,
        "language": language,
        "stats": {
            "extracted_count": len(extracted),
            "stub_count": len(stubs),
            "total_lines": total_lines,
        },
    }


def _ensure_call_graph(
    project_dir: str,
    language: str,
    auto_build: bool,
) -> dict[str, list[str]]:
    """Ensure call graph exists, building if necessary."""
    # Try to load cached call graph
    graph = load_call_graph(project_dir)

    if graph is not None:
        return graph

    if not auto_build:
        # No graph and auto_build disabled - return empty graph
        return {}

    # Build call graph
    build_graph(project_dir, language=language)

    # Load it
    graph = load_call_graph(project_dir)

    return graph if graph is not None else {}


def _generate_empty_harness(language: str) -> str:
    """Generate empty harness comment."""
    if language == "python":
        return '"""AUTO-GENERATED TEST HARNESS\nNo functions found in file.\n"""'
    else:
        return "/* AUTO-GENERATED TEST HARNESS\n * No functions found in file.\n */"
