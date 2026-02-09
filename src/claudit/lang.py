"""Language detection and Pygments lexer mapping shared across skills."""

from __future__ import annotations

from pathlib import Path

from pygments.lexers import CLexer, JavaLexer, PythonLexer


EXT_MAP = {
    ".c": "c",
    ".h": "c",
    ".java": "java",
    ".py": "python",
}

LEXER_MAP = {
    "c": CLexer,
    "java": JavaLexer,
    "python": PythonLexer,
}


def detect_language(project_dir: str) -> str:
    """Auto-detect the dominant language of a project by file extension counts."""
    root = Path(project_dir).resolve()

    counts = {"c": 0, "java": 0, "python": 0}

    for f in root.rglob("*"):
        if f.is_file() and f.suffix in EXT_MAP:
            counts[EXT_MAP[f.suffix]] += 1

    if max(counts.values()) == 0:
        return "c"  # default

    return max(counts, key=lambda k: counts[k])


def load_overrides(path: str | None) -> dict[str, list[str]] | None:
    """Load manual override edges from a JSON file."""
    if path is None:
        return None
    import json
    p = Path(path)
    if not p.exists():
        return None
    data = json.loads(p.read_text())
    if not isinstance(data, dict):
        return None
    return data
