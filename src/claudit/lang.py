"""Language detection utilities shared across skills."""

from __future__ import annotations

from pathlib import Path


EXT_MAP = {
    ".c": "c",
    ".h": "c",
    ".java": "java",
    ".py": "python",
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
