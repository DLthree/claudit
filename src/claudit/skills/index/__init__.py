"""Index management skill – create, query, and inspect GNU Global indexes.

Public API
----------
- create(project_dir, *, force=False) -> dict
- list_symbols(project_dir, *, auto_index=True) -> dict
- get_body(project_dir, function, *, language=None, auto_index=True) -> dict | None
- lookup(project_dir, symbol, *, kind="both", auto_index=True) -> dict
"""

from __future__ import annotations

from typing import Any

from claudit.errors import IndexNotFoundError
from claudit.lang import detect_language
from claudit.skills.index.indexer import (
    FunctionDef,
    FunctionBody,
    ensure_index as _ensure_index,
    find_definition as _find_definition,
    find_references as _find_references,
    get_function_body as _get_function_body,
    list_symbols as _list_symbols,
    gtags_mtime,
    _find_project_root,
)


def _require_index(project_dir: str, auto_index: bool) -> None:
    """Ensure GTAGS exists, or raise if auto_index is disabled."""
    from pathlib import Path

    if auto_index:
        _ensure_index(project_dir)
    else:
        root = Path(project_dir).resolve()
        if not (root / "GTAGS").exists():
            raise IndexNotFoundError(
                f"No index found at {root}. Run: claudit index create {project_dir}"
            )


def create(project_dir: str, *, force: bool = False) -> dict[str, Any]:
    """Create or update a GNU Global index.

    Returns status dict with keys: status, project_dir, gtags_mtime.
    """
    from pathlib import Path
    import os
    import subprocess

    root = _find_project_root(project_dir)
    gtags_file = root / "GTAGS"

    if gtags_file.exists() and not force:
        return {
            "status": "exists",
            "project_dir": str(root),
            "gtags_mtime": gtags_mtime(str(root)),
        }

    # Remove stale index files when forcing
    if force:
        for f in ("GTAGS", "GRTAGS", "GPATH"):
            (root / f).unlink(missing_ok=True)

    _ensure_index(str(root))

    status = "rebuilt" if force else "created"
    return {
        "status": status,
        "project_dir": str(root),
        "gtags_mtime": gtags_mtime(str(root)),
    }


def list_symbols(
    project_dir: str, *, auto_index: bool = True
) -> dict[str, Any]:
    """List all symbols in the project index.

    Returns dict with keys: symbols, count, project_dir.
    """
    _require_index(project_dir, auto_index)
    symbols = _list_symbols(project_dir)
    return {
        "symbols": symbols,
        "count": len(symbols),
        "project_dir": str(_find_project_root(project_dir)),
    }


def get_body(
    project_dir: str,
    function: str,
    *,
    language: str | None = None,
    auto_index: bool = True,
) -> dict[str, Any] | None:
    """Get function body source code.

    Returns dict with function metadata and source, or None if not found.
    """
    _require_index(project_dir, auto_index)

    if language is None:
        language = detect_language(project_dir)

    defs = _find_definition(function, project_dir)
    if not defs:
        return None

    body = _get_function_body(defs[0], project_dir, language)
    if body is None:
        return None

    return {
        "function": function,
        "file": body.file,
        "start_line": body.start_line,
        "end_line": body.end_line,
        "source": body.source,
        "language": language,
    }


def lookup(
    project_dir: str,
    symbol: str,
    *,
    kind: str = "both",
    auto_index: bool = True,
) -> dict[str, Any]:
    """Look up definitions and/or references for a symbol.

    Args:
        kind: "definitions", "references", or "both" (default).

    Returns dict with keys: symbol, definitions, references.
    """
    _require_index(project_dir, auto_index)

    result: dict[str, Any] = {"symbol": symbol}

    if kind in ("both", "definitions"):
        defs = _find_definition(symbol, project_dir)
        result["definitions"] = [
            {"name": d.name, "file": d.file, "line": d.line} for d in defs
        ]

    if kind in ("both", "references"):
        refs = _find_references(symbol, project_dir)
        result["references"] = [
            {"name": r.name, "file": r.file, "line": r.line} for r in refs
        ]

    return result
