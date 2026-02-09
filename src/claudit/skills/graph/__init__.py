"""Call graph skill – build, inspect, and query call graphs.

Public API
----------
- build(project_dir, *, language=None, overrides_path=None, force=False) -> dict
- show(project_dir, *, auto_build=True) -> dict
- callees(project_dir, function, *, auto_build=True) -> dict
- callers(project_dir, function, *, auto_build=True) -> dict
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from claudit.errors import GraphNotFoundError
from claudit.lang import detect_language, load_overrides
from claudit.skills.index.indexer import ensure_index
from claudit.skills.graph.cache import load_call_graph, save_call_graph
from claudit.skills.graph.callgraph import build_call_graph


def _require_graph(project_dir: str, auto_build: bool) -> dict[str, list[str]]:
    """Load or build the call graph."""
    graph = load_call_graph(project_dir)
    if graph is not None:
        return graph

    if not auto_build:
        raise GraphNotFoundError(
            f"No call graph found. Run: claudit graph build {project_dir}"
        )

    ensure_index(project_dir)
    lang = detect_language(project_dir)
    graph = build_call_graph(project_dir, lang)
    save_call_graph(project_dir, graph)
    return graph


def build(
    project_dir: str,
    *,
    language: str | None = None,
    overrides_path: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Build a call graph for the project."""
    ensure_index(project_dir)

    if language is None:
        language = detect_language(project_dir)

    overrides = load_overrides(overrides_path)

    # Check cache first (unless forced or overrides present)
    if not force and overrides is None:
        cached = load_call_graph(project_dir)
        if cached is not None:
            edge_count = sum(len(v) for v in cached.values())
            return {
                "status": "cached",
                "node_count": len(cached),
                "edge_count": edge_count,
                "language": language,
                "project_dir": str(Path(project_dir).resolve()),
            }

    graph = build_call_graph(project_dir, language, overrides=overrides)
    save_call_graph(project_dir, graph)

    edge_count = sum(len(v) for v in graph.values())
    return {
        "status": "built",
        "node_count": len(graph),
        "edge_count": edge_count,
        "language": language,
        "project_dir": str(Path(project_dir).resolve()),
    }


def show(
    project_dir: str,
    *,
    auto_build: bool = True,
) -> dict[str, Any]:
    """Return the full call graph."""
    graph = _require_graph(project_dir, auto_build)
    edge_count = sum(len(v) for v in graph.values())
    return {
        "graph": graph,
        "node_count": len(graph),
        "edge_count": edge_count,
    }


def callees(
    project_dir: str,
    function: str,
    *,
    auto_build: bool = True,
) -> dict[str, Any]:
    """List direct callees of a function."""
    graph = _require_graph(project_dir, auto_build)
    callee_list = graph.get(function, [])
    return {
        "function": function,
        "callees": callee_list,
        "count": len(callee_list),
    }


def callers(
    project_dir: str,
    function: str,
    *,
    auto_build: bool = True,
) -> dict[str, Any]:
    """List direct callers of a function (reverse lookup)."""
    graph = _require_graph(project_dir, auto_build)
    caller_list = sorted(
        caller for caller, targets in graph.items() if function in targets
    )
    return {
        "function": function,
        "callers": caller_list,
        "count": len(caller_list),
    }
