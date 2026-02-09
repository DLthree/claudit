"""Pygments-based source code highlighting and annotation."""

from __future__ import annotations

from typing import Any

from pygments import highlight as _pygments_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import CLexer, JavaLexer, PythonLexer, get_lexer_by_name

from claudit.lang import detect_language
from claudit.skills.index.indexer import (
    find_definition,
    get_function_body,
    FunctionBody,
)


LEXER_MAP = {
    "c": CLexer,
    "java": JavaLexer,
    "python": PythonLexer,
}

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
    """Highlight all functions in a call path with per-hop colors and notes.

    Args:
        path: List of function names forming the call path.

    Returns dict with highlights array and metadata.
    """
    if language is None:
        language = detect_language(project_dir)

    highlights: list[dict[str, Any]] = []

    for hop_index, func_name in enumerate(path):
        color = HOP_COLORS[hop_index % len(HOP_COLORS)]
        entry: dict[str, Any] = {
            "function": func_name,
            "hop_index": hop_index,
            "color": color,
        }

        defs = find_definition(func_name, project_dir)
        if not defs:
            entry.update({
                "file": "<unknown>",
                "start_line": 0,
                "end_line": 0,
                "source": "",
                "highlighted_html": "",
                "note": f"Definition not found for '{func_name}'",
            })
            highlights.append(entry)
            continue

        body = get_function_body(defs[0], project_dir, language)
        if body is None:
            entry.update({
                "file": defs[0].file,
                "start_line": defs[0].line,
                "end_line": defs[0].line,
                "source": "",
                "highlighted_html": "",
                "note": f"Could not extract body for '{func_name}'",
            })
            highlights.append(entry)
            continue

        highlighted_html = _highlight_source(body.source, language, style)

        # Build a note describing this hop's role in the path
        note = _build_hop_note(hop_index, func_name, path)

        # Find the call site to the next function in the path
        call_site = None
        if hop_index < len(path) - 1:
            next_func = path[hop_index + 1]
            call_site = _find_call_site(body, next_func)

        entry.update({
            "file": body.file,
            "start_line": body.start_line,
            "end_line": body.end_line,
            "source": body.source,
            "highlighted_html": highlighted_html,
            "note": note,
        })
        if call_site is not None:
            entry["call_site"] = call_site

        highlights.append(entry)

    return {
        "highlights": highlights,
        "style": style,
        "path_length": len(path),
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
    """Find where in the function body the callee is called."""
    lines = body.source.splitlines()
    for i, line in enumerate(lines):
        if callee_name in line and "(" in line:
            return {
                "line": body.start_line + i,
                "callee": callee_name,
                "snippet": line.strip(),
            }
    return None
