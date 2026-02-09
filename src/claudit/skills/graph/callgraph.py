"""Call graph construction using GNU Global + Pygments lexers.

For each function:
1. Get definition + body bounds via Global
2. Tokenize body with the appropriate Pygments lexer
3. Extract function-call tokens
4. Resolve callees via Global symbol lookup
5. Handle C function pointers and ambiguous calls
"""

from __future__ import annotations

import re
import subprocess
import shutil
from pathlib import Path
from typing import Any

from pygments.lexers import CLexer, JavaLexer, PythonLexer
from pygments.token import Token

from claudit.skills.index.indexer import (
    FunctionDef,
    find_definition,
    get_function_body,
    list_symbols,
)


LEXER_MAP = {
    "c": CLexer,
    "java": JavaLexer,
    "python": PythonLexer,
}


def build_call_graph(
    project_dir: str,
    language: str,
    overrides: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Build a full call graph for the project.

    Returns a dict mapping caller function name -> list of callee names.
    """
    symbols = list_symbols(project_dir)
    graph: dict[str, list[str]] = {}
    symbol_set = set(symbols)

    for sym in symbols:
        callees = _callees_of(sym, project_dir, language, symbol_set)
        if callees:
            graph[sym] = callees

    # C function pointer handling
    if language == "c":
        fp_edges = _resolve_c_function_pointers(project_dir, symbol_set)
        for caller, targets in fp_edges.items():
            existing = set(graph.get(caller, []))
            existing.update(targets)
            graph[caller] = sorted(existing)

    # Merge manual overrides
    if overrides:
        for caller, targets in overrides.items():
            existing = set(graph.get(caller, []))
            existing.update(targets)
            graph[caller] = sorted(existing)

    return graph


def _callees_of(
    func_name: str,
    project_dir: str,
    language: str,
    known_symbols: set[str],
) -> list[str]:
    """Extract function calls from the body of func_name."""
    defs = find_definition(func_name, project_dir)
    if not defs:
        return []

    # Use first definition
    func_def = defs[0]
    body = get_function_body(func_def, project_dir, language)
    if body is None or not body.source.strip():
        return []

    return _extract_calls_from_source(body.source, language, known_symbols)


def _extract_calls_from_source(
    source: str,
    language: str,
    known_symbols: set[str],
) -> list[str]:
    """Tokenize source with Pygments and extract function call names."""
    lexer_cls = LEXER_MAP.get(language)
    if lexer_cls is None:
        return []

    lexer = lexer_cls(stripnl=False, ensurenl=False)
    tokens = list(lexer.get_tokens(source))

    calls: set[str] = set()

    for i, (ttype, value) in enumerate(tokens):
        if ttype in Token.Name and value in known_symbols:
            # Look ahead for a '(' to confirm it's a call
            for j in range(i + 1, min(i + 5, len(tokens))):
                next_type, next_val = tokens[j]
                if next_type in Token.Text or next_type in Token.Comment:
                    continue
                if next_val == "(":
                    calls.add(value)
                break

    return sorted(calls)


def _resolve_c_function_pointers(
    project_dir: str,
    known_symbols: set[str],
) -> dict[str, list[str]]:
    """Scan for C struct field assignments that look like function pointers.

    Pattern: .field = func_name  or  ->field = func_name
    Uses ripgrep for speed, falls back to nothing if rg unavailable.
    """
    rg = shutil.which("rg")
    if rg is None:
        return {}

    root = Path(project_dir).resolve()
    # Match patterns like: .ops = my_func  or  ->handler = callback
    result = subprocess.run(
        [
            rg,
            "--no-heading",
            "-n",
            r"(?:->|\.)(\w+)\s*=\s*(\w+)",
            "--type", "c",
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
    )

    edges: dict[str, list[str]] = {}
    pattern = re.compile(r"(?:->|\.)(\w+)\s*=\s*(\w+)")

    for line in result.stdout.splitlines():
        m = pattern.search(line)
        if m:
            _field_name = m.group(1)
            target = m.group(2)
            if target in known_symbols:
                file_match = re.match(r"^(.+?):(\d+):", line)
                if file_match:
                    caller = _find_enclosing_function(
                        root / file_match.group(1),
                        int(file_match.group(2)),
                        project_dir,
                    )
                    if caller:
                        edges.setdefault(caller, []).append(target)

    return edges


def _find_enclosing_function(
    filepath: Path,
    line_no: int,
    project_dir: str,
) -> str | None:
    """Best-effort: find which function encloses a given line.

    Uses `global -f` to list definitions in file, picks the nearest
    definition above line_no.
    """
    global_bin = shutil.which("global")
    if global_bin is None:
        return None

    root = Path(project_dir).resolve()
    try:
        relpath = filepath.relative_to(root)
    except ValueError:
        return None

    result = subprocess.run(
        [global_bin, "-f", str(relpath)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )

    best_name: str | None = None
    best_line = 0

    for out_line in result.stdout.strip().splitlines():
        parts = out_line.split()
        if len(parts) >= 3:
            name = parts[0]
            try:
                defline = int(parts[1])
            except ValueError:
                continue
            if defline <= line_no and defline > best_line:
                best_line = defline
                best_name = name

    return best_name
