"""Caching layer for reachability analysis.

Stores memoized Global results and parsed call graph edges in
.cache/<project_hash>/ keyed on project path + GTAGS mtime.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from claudit.skills.reachability.indexer import gtags_mtime


def _project_hash(project_dir: str) -> str:
    """Deterministic hash for a project path."""
    return hashlib.sha256(
        Path(project_dir).resolve().as_posix().encode()
    ).hexdigest()[:16]


def _cache_dir(project_dir: str) -> Path:
    root = Path(project_dir).resolve()
    return root / ".cache" / _project_hash(project_dir)


def _cache_key(project_dir: str) -> str:
    """Key incorporating GTAGS mtime so stale caches are ignored."""
    mtime = gtags_mtime(project_dir)
    return f"{_project_hash(project_dir)}:{mtime}"


def load_call_graph(project_dir: str) -> dict[str, list[str]] | None:
    """Load cached call graph if it exists and is fresh."""
    d = _cache_dir(project_dir)
    meta_file = d / "callgraph_meta.json"
    graph_file = d / "callgraph.json"

    if not meta_file.exists() or not graph_file.exists():
        return None

    meta = json.loads(meta_file.read_text())
    if meta.get("key") != _cache_key(project_dir):
        return None

    return json.loads(graph_file.read_text())


def save_call_graph(project_dir: str, graph: dict[str, list[str]]) -> None:
    """Persist call graph to disk."""
    d = _cache_dir(project_dir)
    d.mkdir(parents=True, exist_ok=True)

    meta_file = d / "callgraph_meta.json"
    graph_file = d / "callgraph.json"

    meta_file.write_text(json.dumps({"key": _cache_key(project_dir)}))
    graph_file.write_text(json.dumps(graph))


def load_global_results(project_dir: str) -> dict[str, Any] | None:
    """Load cached Global query results."""
    d = _cache_dir(project_dir)
    meta_file = d / "global_meta.json"
    results_file = d / "global_results.json"

    if not meta_file.exists() or not results_file.exists():
        return None

    meta = json.loads(meta_file.read_text())
    if meta.get("key") != _cache_key(project_dir):
        return None

    return json.loads(results_file.read_text())


def save_global_results(project_dir: str, results: dict[str, Any]) -> None:
    """Persist Global query results to disk."""
    d = _cache_dir(project_dir)
    d.mkdir(parents=True, exist_ok=True)

    meta_file = d / "global_meta.json"
    results_file = d / "global_results.json"

    meta_file.write_text(json.dumps({"key": _cache_key(project_dir)}))
    results_file.write_text(json.dumps(results))
