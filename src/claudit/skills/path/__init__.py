"""Path finding skill – find call paths between functions.

Public API
----------
- find(project_dir, source, target, *, max_depth=10, annotate=True,
       auto_build=True, language=None, overrides_path=None) -> dict
"""

from __future__ import annotations

from typing import Any

from claudit.errors import GraphNotFoundError
from claudit.lang import load_overrides
from claudit.skills.graph import build as build_graph
from claudit.skills.graph.cache import load_call_graph
from claudit.skills.path.pathfinder import find_all_paths, annotate_path


def find(
    project_dir: str,
    source: str,
    target: str,
    *,
    max_depth: int = 10,
    annotate: bool = True,
    auto_build: bool = True,
    language: str | None = None,
    overrides_path: str | None = None,
) -> dict[str, Any]:
    """Find all call paths from source to target function."""
    cache_used = False
    graph = load_call_graph(project_dir)
    overrides = load_overrides(overrides_path)

    if graph is not None and overrides is None:
        cache_used = True
    else:
        if not auto_build and graph is None:
            raise GraphNotFoundError(
                f"No call graph found. Run: claudit graph build {project_dir}"
            )
        build_graph(
            project_dir,
            language=language,
            overrides_path=overrides_path,
            force=(overrides is not None),
        )
        graph = load_call_graph(project_dir)
        if graph is None:
            graph = {}

    raw_paths = find_all_paths(graph, source, target, max_depth)

    paths = []
    for rp in raw_paths:
        if annotate:
            cp = annotate_path(rp, project_dir)
            paths.append({
                "hops": [
                    {
                        "function": h.function,
                        "file": h.file,
                        "line": h.line,
                        "snippet": h.snippet,
                    }
                    for h in cp.hops
                ],
                "length": len(cp.hops),
            })
        else:
            paths.append({
                "hops": rp,
                "length": len(rp),
            })

    return {
        "source": source,
        "target": target,
        "paths": paths,
        "path_count": len(paths),
        "cache_used": cache_used,
    }
