"""Core orchestration for the reachability skill.

Ties together indexing, call graph construction, caching, and path finding.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from claudit.skills.reachability.cache import (
    load_call_graph,
    save_call_graph,
)
from claudit.skills.reachability.callgraph import build_call_graph, detect_language
from claudit.skills.reachability.indexer import ensure_index
from claudit.skills.reachability.pathfinder import annotate_path, find_all_paths


def find_reachability(
    source: str,
    target: str,
    project_dir: str,
    language: str | None = None,
    max_depth: int = 10,
    overrides_path: str | None = None,
) -> dict[str, Any]:
    """Main entry point: find call paths from source to target.

    Returns the result dict matching the specified output format:
    {
        "paths": [ { "hops": [ { "function", "file", "line", "snippet" }, ... ] } ],
        "cache_used": bool
    }
    """
    # 1. Ensure index exists
    ensure_index(project_dir)

    # 2. Detect language if not provided
    if language is None:
        language = detect_language(project_dir)

    # 3. Load overrides
    overrides = _load_overrides(overrides_path)

    # 4. Build or load call graph
    cache_used = False
    graph = load_call_graph(project_dir)
    if graph is not None and overrides is None:
        cache_used = True
    else:
        graph = build_call_graph(project_dir, language, overrides)
        save_call_graph(project_dir, graph)

    # 5. Find paths
    raw_paths = find_all_paths(graph, source, target, max_depth)

    # 6. Annotate
    paths = []
    for rp in raw_paths:
        cp = annotate_path(rp, project_dir)
        paths.append(
            {
                "hops": [
                    {
                        "function": h.function,
                        "file": h.file,
                        "line": h.line,
                        "snippet": h.snippet,
                    }
                    for h in cp.hops
                ]
            }
        )

    return {
        "paths": paths,
        "cache_used": cache_used,
    }


def _load_overrides(path: str | None) -> dict[str, list[str]] | None:
    """Load manual override edges from a JSON file."""
    if path is None:
        return None
    p = Path(path)
    if not p.exists():
        return None
    data = json.loads(p.read_text())
    if not isinstance(data, dict):
        return None
    return data
