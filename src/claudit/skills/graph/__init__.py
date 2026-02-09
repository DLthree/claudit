"""Call graph skill – build, inspect, and query call graphs.

Public API
----------
- build(project_dir, *, language=None, overrides=None, force=False, auto_index=True) -> dict
- show(project_dir, *, auto_build=True) -> dict
- callees(project_dir, function, *, auto_build=True) -> dict
- callers(project_dir, function, *, auto_build=True) -> dict
"""

from __future__ import annotations

import json as _json
from pathlib import Path
from typing import Any

from claudit.errors import GraphNotFoundError
from claudit.lang import detect_language
from claudit.skills.index import create as _ensure_index
from claudit.skills.graph.cache import (
    load_call_graph as _load_graph,
    save_call_graph as _save_graph,
)
from claudit.skills.graph.callgraph import build_call_graph as _build_graph


def _require_graph(project_dir: str, auto_build: bool, **build_kwargs: Any) -> dict[str, list[str]]:
    """Load or build the call graph."""
    graph = _load_graph(project_dir)
    if graph is not None:
        return graph

    if not auto_build:
        raise GraphNotFoundError(
            f"No call graph found. Run: claudit graph build {project_dir}"
        )

    # Auto-build: ensure index first, then build graph
    _ensure_index(project_dir)
    lang = build_kwargs.get("language") or detect_language(project_dir)
    graph = _build_graph(project_dir, lang, overrides=build_kwargs.get("overrides"))
    _save_graph(project_dir, graph)
    return graph


def _load_overrides(path: str | None) -> dict[str, list[str]] | None:
    """Load manual override edges from a JSON file."""
    if path is None:
        return None
    p = Path(path)
    if not p.exists():
        return None
    data = _json.loads(p.read_text())
    if not isinstance(data, dict):
        return None
    return data


def build(
    project_dir: str,
    *,
    language: str | None = None,
    overrides_path: str | None = None,
    force: bool = False,
    auto_index: bool = True,
) -> dict[str, Any]:
    """Build a call graph for the project.

    Returns status dict with keys: status, node_count, edge_count, language, project_dir.
    """
    if auto_index:
        _ensure_index(project_dir)

    if language is None:
        language = detect_language(project_dir)

    overrides = _load_overrides(overrides_path)

    # Check cache first (unless forced or overrides present)
    if not force and overrides is None:
        cached = _load_graph(project_dir)
        if cached is not None:
            edge_count = sum(len(v) for v in cached.values())
            return {
                "status": "cached",
                "node_count": len(cached),
                "edge_count": edge_count,
                "language": language,
                "project_dir": str(Path(project_dir).resolve()),
            }

    graph = _build_graph(project_dir, language, overrides=overrides)
    _save_graph(project_dir, graph)

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
    """Return the full call graph as JSON.

    Returns dict with keys: graph, node_count, edge_count.
    """
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
    """List direct callees of a function.

    Returns dict with keys: function, callees, count.
    """
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
    """List direct callers of a function (reverse lookup).

    Returns dict with keys: function, callers, count.
    """
    graph = _require_graph(project_dir, auto_build)
    # Build reverse index
    caller_list = sorted(
        caller for caller, targets in graph.items() if function in targets
    )
    return {
        "function": function,
        "callers": caller_list,
        "count": len(caller_list),
    }
