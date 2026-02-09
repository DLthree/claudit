"""BFS-based path finding over a call graph.

Given a call graph (caller -> [callees]), find all paths from source
function to target function within a max_depth limit.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from claudit.skills.index.indexer import find_definition, FunctionDef


@dataclass
class Hop:
    """One step in a call chain."""

    function: str
    file: str
    line: int
    snippet: str


@dataclass
class CallPath:
    """A complete path from source to target."""

    hops: list[Hop] = field(default_factory=list)


def find_all_paths(
    graph: dict[str, list[str]],
    source: str,
    target: str,
    max_depth: int = 10,
) -> list[list[str]]:
    """BFS to find all paths from source to target, up to max_depth hops.

    Returns list of paths, where each path is a list of function names.
    """
    if source == target:
        return [[source]]

    results: list[list[str]] = []
    queue: deque[list[str]] = deque([[source]])

    while queue:
        path = queue.popleft()

        if len(path) > max_depth:
            continue

        current = path[-1]
        callees = graph.get(current, [])

        for callee in callees:
            if callee in path:
                # Skip cycles
                continue
            new_path = path + [callee]
            if callee == target:
                results.append(new_path)
            elif len(new_path) <= max_depth:
                queue.append(new_path)

    return results


def annotate_path(
    path: list[str],
    project_dir: str,
) -> CallPath:
    """Add file/line/snippet info to each hop in a path."""
    hops: list[Hop] = []
    for func_name in path:
        defs = find_definition(func_name, project_dir)
        if defs:
            d = defs[0]
            # Read the line for a snippet
            snippet = _read_line(project_dir, d.file, d.line)
            hops.append(
                Hop(
                    function=func_name,
                    file=d.file,
                    line=d.line,
                    snippet=snippet,
                )
            )
        else:
            hops.append(
                Hop(function=func_name, file="<unknown>", line=0, snippet="")
            )
    return CallPath(hops=hops)


def _read_line(project_dir: str, filepath: str, line_no: int) -> str:
    """Read a single line from a file."""
    from pathlib import Path

    full = Path(project_dir).resolve() / filepath
    if not full.exists():
        return ""
    try:
        lines = full.read_text(errors="replace").splitlines()
        if 0 < line_no <= len(lines):
            return lines[line_no - 1].strip()
    except OSError:
        pass
    return ""
