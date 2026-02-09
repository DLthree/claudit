"""Test harness generation skill - extraction and analysis utilities.

This skill provides tools to help LLMs iteratively build test harnesses
by extracting code and analyzing dependencies. The LLM makes decisions
about what to stub vs extract based on compilation errors.

Public API
----------
Extraction:
- extract_function(project_dir, function_name, language=None) -> ExtractedFunction | None
- extract_functions(project_dir, function_names, language=None) -> list[ExtractedFunction]
- extract_file(project_dir, filepath, language=None) -> list[ExtractedFunction]
- list_functions_in_file(project_dir, filepath) -> list[dict]

Analysis (diagnostic aids):
- analyze_dependencies(project_dir, function_names, depth=1) -> DependencySet
- get_function_signature(project_dir, function_name, language=None) -> FunctionSignature | None
- get_function_callees(project_dir, function_name) -> list[str]
"""

from __future__ import annotations

from claudit.skills.harness.extractor import (
    ExtractedFunction,
    extract_target_functions,
    extract_functions_from_file,
    list_functions_in_file,
)
from claudit.skills.harness.dependency_analyzer import (
    DependencySet,
    analyze_dependencies as _analyze_dependencies,
)
from claudit.skills.harness.signature_extractor import (
    FunctionSignature,
    Parameter,
    extract_signature,
)

# Re-export for convenience
__all__ = [
    "ExtractedFunction",
    "DependencySet",
    "FunctionSignature",
    "Parameter",
    "extract_function",
    "extract_functions",
    "extract_file",
    "list_functions_in_file",
    "analyze_dependencies",
    "get_function_signature",
    "get_function_callees",
]


def extract_function(
    project_dir: str,
    function_name: str,
    language: str | None = None,
) -> ExtractedFunction | None:
    """Extract a single function verbatim.

    Args:
        project_dir: Project directory path
        function_name: Name of function to extract
        language: Target language (c, java, python) - auto-detected if None

    Returns:
        ExtractedFunction if found, None otherwise
    """
    from claudit.lang import detect_language

    if language is None:
        language = detect_language(project_dir)

    result = extract_target_functions(project_dir, [function_name], language)
    return result[0] if result else None


def extract_functions(
    project_dir: str,
    function_names: list[str],
    language: str | None = None,
) -> list[ExtractedFunction]:
    """Extract multiple functions verbatim.

    Args:
        project_dir: Project directory path
        function_names: List of function names to extract
        language: Target language (c, java, python) - auto-detected if None

    Returns:
        List of ExtractedFunction objects

    Raises:
        ValueError: If a function cannot be found
    """
    from claudit.lang import detect_language

    if language is None:
        language = detect_language(project_dir)

    return extract_target_functions(project_dir, function_names, language)


def extract_file(
    project_dir: str,
    filepath: str,
    language: str | None = None,
) -> list[ExtractedFunction]:
    """Extract all functions from a file.

    Args:
        project_dir: Project directory path
        filepath: Relative path to source file from project root
        language: Target language (c, java, python) - auto-detected if None

    Returns:
        List of ExtractedFunction objects

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    from claudit.lang import detect_language

    if language is None:
        language = detect_language(project_dir)

    return extract_functions_from_file(project_dir, filepath, language)


def analyze_dependencies(
    project_dir: str,
    function_names: list[str],
    depth: int = 1,
) -> DependencySet:
    """Analyze dependencies without full orchestration.

    Args:
        project_dir: Project directory path
        function_names: List of function names to analyze
        depth: How many levels deep to analyze (default: 1)

    Returns:
        DependencySet with stub_functions, dependency_map, excluded_stdlib
    """
    from claudit.lang import detect_language
    from claudit.skills.index.indexer import ensure_index
    from claudit.skills.graph import build as build_graph
    from claudit.skills.graph.cache import load_call_graph

    language = detect_language(project_dir)
    ensure_index(project_dir)

    # Ensure call graph exists
    graph = load_call_graph(project_dir)
    if graph is None:
        build_graph(project_dir, language=language)
        graph = load_call_graph(project_dir) or {}

    return _analyze_dependencies(
        project_dir, set(function_names), graph, stub_depth=depth
    )


def get_function_signature(
    project_dir: str,
    function_name: str,
    language: str | None = None,
) -> FunctionSignature | None:
    """Get function signature for stubbing.

    Args:
        project_dir: Project directory path
        function_name: Name of function to get signature for
        language: Target language (c, java, python) - auto-detected if None

    Returns:
        FunctionSignature if found, None otherwise
    """
    from pathlib import Path
    from claudit.lang import detect_language
    from claudit.skills.index import lookup

    if language is None:
        language = detect_language(project_dir)

    # Find function in project
    result = lookup(project_dir, function_name, kind="definitions", auto_index=True)
    if not result.get("definitions"):
        return None

    defn = result["definitions"][0]
    filepath = Path(project_dir) / defn["file"]

    return extract_signature(str(filepath), function_name, language)


def get_function_callees(
    project_dir: str,
    function_name: str,
) -> list[str]:
    """Get direct callees of a function.

    Args:
        project_dir: Project directory path
        function_name: Name of function to get callees for

    Returns:
        List of function names called by the target function
    """
    from claudit.skills.graph.cache import load_call_graph

    graph = load_call_graph(project_dir)
    if graph is None:
        return []

    return graph.get(function_name, [])
