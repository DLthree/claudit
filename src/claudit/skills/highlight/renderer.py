"""Pygments-based source code highlighting and annotation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pygments import highlight as _pygments_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from claudit.lang import detect_language, LEXER_MAP
from claudit.skills.index.indexer import (
    find_definition,
    get_function_body,
    FunctionBody,
    FunctionDef,
)

RESULTS_FORMAT_VERSION = "0.1.0"

# Distinct colors for hop visualization
HOP_COLORS = [
    "#FF6B6B",  # red
    "#4ECDC4",  # teal
    "#45B7D1",  # blue
    "#96CEB4",  # sage
    "#FFEAA7",  # yellow
    "#DDA0DD",  # plum
    "#98D8C8",  # mint
    "#F7DC6F",  # gold
    "#BB8FCE",  # lavender
    "#85C1E9",  # sky
]


def _hex_to_rgba(hex_color: str, alpha: float = 0.3) -> str:
    """Convert a hex color like '#FF6B6B' to rgba(r, g, b, alpha)."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return f"rgba(0, 0, 0, {alpha})"
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def highlight_function(
    project_dir: str,
    function: str,
    *,
    language: str | None = None,
    style: str = "monokai",
) -> dict[str, Any] | None:
    """Highlight a single function's source code.

    Returns dict with raw source and highlighted HTML, or None if not found.
    """
    if language is None:
        language = detect_language(project_dir)

    defs = find_definition(function, project_dir)
    if not defs:
        return None

    body = get_function_body(defs[0], project_dir, language)
    if body is None:
        return None

    highlighted_html = _highlight_source(body.source, language, style)

    return {
        "function": function,
        "file": body.file,
        "start_line": body.start_line,
        "end_line": body.end_line,
        "source": body.source,
        "highlighted_html": highlighted_html,
        "language": language,
    }


def highlight_path(
    project_dir: str,
    path: list[str],
    *,
    language: str | None = None,
    style: str = "monokai",
) -> dict[str, Any]:
    """Produce a result set for a call path in RESULTS_FORMAT (metadata + results).

    Each result is a single span: either a function definition or a call site.
    Only these call-chain locations are included, not full function bodies.

    Returns dict with metadata and results conforming to RESULTS_FORMAT.
    """
    if language is None:
        language = detect_language(project_dir)

    results: list[dict[str, Any]] = []
    result_id = 0

    for hop_index, func_name in enumerate(path):
        color_hex = HOP_COLORS[hop_index % len(HOP_COLORS)]
        color_rgba = _hex_to_rgba(color_hex)
        note = _build_hop_note(hop_index, func_name, path)

        defs = find_definition(func_name, project_dir)
        if not defs:
            result_id += 1
            results.append({
                "ID": str(result_id),
                "description": f"definition of {func_name}",
                "notes": f"Definition not found for '{func_name}'",
                "category": "Call path",
                "severity": "info",
                "filename": "<unknown>",
                "linenum": 0,
                "col_start": 1,
                "col_end": 1,
                "function": func_name,
                "color": color_rgba,
            })
            continue

        func_def = defs[0]
        linenum, col_start, col_end = _definition_span(func_def, project_dir)

        result_id += 1
        results.append({
            "ID": str(result_id),
            "description": f"definition of {func_name}",
            "notes": note,
            "category": "Call path",
            "severity": "info",
            "filename": func_def.file,
            "linenum": linenum,
            "col_start": col_start,
            "col_end": col_end,
            "function": func_name,
            "color": color_rgba,
        })

        if hop_index < len(path) - 1:
            next_func = path[hop_index + 1]
            body = get_function_body(func_def, project_dir, language)
            if body is not None:
                call_site = _find_call_site(body, next_func)
                if call_site is not None:
                    result_id += 1
                    results.append({
                        "ID": str(result_id),
                        "description": f"call to {next_func}",
                        "notes": note,
                        "category": "Call path",
                        "severity": "info",
                        "filename": body.file,
                        "linenum": call_site["line"],
                        "col_start": call_site["col_start"],
                        "col_end": call_site["col_end"],
                        "function": func_name,
                        "color": color_rgba,
                    })

    metadata = {
        "author": "claudit highlight",
        "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "tool": "claudit",
        "version": RESULTS_FORMAT_VERSION,
    }

    return {
        "metadata": metadata,
        "results": results,
    }


def _highlight_source(source: str, language: str, style: str) -> str:
    """Apply Pygments syntax highlighting to source code."""
    lexer_cls = LEXER_MAP.get(language)
    if lexer_cls is None:
        try:
            lexer = get_lexer_by_name(language)
        except Exception:
            return source
    else:
        lexer = lexer_cls()

    formatter = HtmlFormatter(style=style, nowrap=True)
    return _pygments_highlight(source, lexer, formatter)


def _definition_span(
    func_def: FunctionDef, project_dir: str, definition_line: str | None = None
) -> tuple[int, int, int]:
    """Return (linenum, col_start, col_end) 1-based for the function name on its definition line.

    If definition_line is not provided, the line is read from the file.
    If the function name cannot be found, returns whole line: col_start=1, col_end=len(line).
    """
    line = definition_line
    if line is None:
        root = Path(project_dir).resolve()
        filepath = root / func_def.file
        if not filepath.exists():
            return (func_def.line, 1, 1)
        try:
            lines = filepath.read_text(errors="replace").splitlines()
        except OSError:
            return (func_def.line, 1, 1)
        idx = func_def.line - 1
        if idx < 0 or idx >= len(lines):
            return (func_def.line, 1, 1)
        line = lines[idx]
    name = func_def.name
    idx = line.find(name)
    if idx == -1:
        return (func_def.line, 1, max(1, len(line)))
    col_start = idx + 1
    col_end = idx + len(name)
    return (func_def.line, col_start, col_end)


def _build_hop_note(hop_index: int, func_name: str, path: list[str]) -> str:
    """Build a human-readable note for a hop in the path."""
    if hop_index == 0:
        if len(path) > 1:
            return f"Entry point: calls {path[1]}()"
        return "Entry point (single-hop path)"
    elif hop_index == len(path) - 1:
        return f"Target: called from {path[hop_index - 1]}()"
    else:
        return f"Intermediate: called from {path[hop_index - 1]}(), calls {path[hop_index + 1]}()"


def _find_call_site(
    body: FunctionBody, callee_name: str
) -> dict[str, Any] | None:
    """Find where in the function body the callee is called.

    Returns line, col_start, col_end (1-based; col_end inclusive), preferring
    the occurrence of callee_name that is followed by '(' (actual call).
    """
    lines = body.source.splitlines()
    for i, line in enumerate(lines):
        idx = 0
        while True:
            idx = line.find(callee_name, idx)
            if idx == -1:
                break
            end = idx + len(callee_name)
            rest = line[end:].lstrip()
            if rest.startswith("("):
                col_start = idx + 1
                col_end = idx + len(callee_name)  # 1-based inclusive
                return {
                    "line": body.start_line + i,
                    "col_start": col_start,
                    "col_end": col_end,
                    "callee": callee_name,
                    "snippet": line.strip(),
                }
            idx = end
    return None
