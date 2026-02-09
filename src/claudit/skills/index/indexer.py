"""GNU Global indexing + Universal Ctags interface.

Handles running gtags, querying definitions/references, and extracting
function body bounds.  Function start/end lines come from Universal Ctags
(``ctags --output-format=json --fields=+ne``), which gives precise bounds
for C, Java, and Python without heuristic brace/indent counting.
"""

from __future__ import annotations

import json as _json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from claudit.errors import (
    GlobalNotFoundError,
    CtagsNotFoundError,
    IndexingError,
)


@dataclass
class FunctionDef:
    """A function definition located by GNU Global."""

    name: str
    file: str
    line: int


@dataclass
class FunctionBody:
    """Bounds of a function body in source."""

    file: str
    start_line: int
    end_line: int
    source: str


def _check_global() -> str:
    """Return path to `global` binary, or raise."""
    path = shutil.which("global")
    if path is None:
        raise GlobalNotFoundError()
    return path


def _check_gtags() -> str:
    """Return path to `gtags` binary, or raise."""
    path = shutil.which("gtags")
    if path is None:
        raise GlobalNotFoundError()
    return path


def _check_ctags() -> str:
    """Return path to Universal Ctags binary, or raise."""
    path = shutil.which("ctags")
    if path is None:
        raise CtagsNotFoundError()
    return path


def ensure_index(project_dir: str) -> Path:
    """Run gtags if GTAGS does not already exist. Return project root Path."""
    root = _find_project_root(project_dir)
    gtags_file = root / "GTAGS"

    if not gtags_file.exists():
        gtags_bin = _check_gtags()
        env = os.environ.copy()
        env["GTAGSFORCECPP"] = "1"  # treat .h as C++
        result = subprocess.run(
            [gtags_bin],
            cwd=str(root),
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise IndexingError(
                f"gtags failed (exit {result.returncode}):\n{result.stderr}"
            )

    return root


def _find_project_root(project_dir: str) -> Path:
    """Resolve the project root directory."""
    p = Path(project_dir).resolve()
    if not p.is_dir():
        raise FileNotFoundError(f"Project directory does not exist: {p}")
    return p


def gtags_mtime(project_dir: str) -> float:
    """Return mtime of GTAGS file, or 0 if absent."""
    gtags = Path(project_dir).resolve() / "GTAGS"
    if gtags.exists():
        return gtags.stat().st_mtime
    return 0.0


def find_definition(name: str, project_dir: str) -> list[FunctionDef]:
    """Use `global -d` to find definition(s) of a symbol."""
    global_bin = _check_global()
    root = Path(project_dir).resolve()
    result = subprocess.run(
        [global_bin, "-d", "--result=grep", name],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    defs: list[FunctionDef] = []
    for line in result.stdout.strip().splitlines():
        m = re.match(r"^(.+?):(\d+):", line)
        if m:
            defs.append(
                FunctionDef(name=name, file=m.group(1), line=int(m.group(2)))
            )
    return defs


def find_references(name: str, project_dir: str) -> list[FunctionDef]:
    """Use `global -r` to find references to a symbol."""
    global_bin = _check_global()
    root = Path(project_dir).resolve()
    result = subprocess.run(
        [global_bin, "-r", "--result=grep", name],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    refs: list[FunctionDef] = []
    for line in result.stdout.strip().splitlines():
        m = re.match(r"^(.+?):(\d+):", line)
        if m:
            refs.append(
                FunctionDef(name=name, file=m.group(1), line=int(m.group(2)))
            )
    return refs


def get_ctags_tags(filepath: str) -> list[dict]:
    """Run Universal Ctags on a single file, return parsed JSON tag list.

    Each element is a dict with at least: name, path, line, kind.
    Function/method tags also have an ``end`` key with the closing line number.
    """
    ctags_bin = _check_ctags()
    result = subprocess.run(
        [
            ctags_bin,
            "--output-format=json",
            "--fields=+ne",
            "-o", "-",
            filepath,
        ],
        capture_output=True,
        text=True,
    )
    tags: list[dict] = []
    for raw_line in result.stdout.splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            tag = _json.loads(raw_line)
            if isinstance(tag, dict) and tag.get("_type") == "tag":
                tags.append(tag)
        except _json.JSONDecodeError:
            continue
    return tags


def _ctags_function_bounds(
    filepath: str, func_name: str, start_line: int
) -> tuple[int, int] | None:
    """Look up (start, end) line numbers for *func_name* at *start_line*.

    Returns ``None`` if ctags doesn't report an ``end`` for this tag.
    """
    tags = get_ctags_tags(filepath)
    # Match on name + line; kind must be function/method/def
    for tag in tags:
        if (
            tag.get("name") == func_name
            and tag.get("line") == start_line
            and "end" in tag
        ):
            return (tag["line"], tag["end"])

    # Fallback: match on name alone (may hit first overload)
    for tag in tags:
        if tag.get("name") == func_name and "end" in tag:
            return (tag["line"], tag["end"])

    return None


def get_function_body(
    func_def: FunctionDef,
    project_dir: str,
    language: str,
) -> FunctionBody | None:
    """Extract the source of a function body using Universal Ctags bounds.

    Runs ``ctags --output-format=json --fields=+ne`` on the file to get
    precise start/end line numbers, then slices the source.
    """
    root = Path(project_dir).resolve()
    filepath = root / func_def.file
    if not filepath.exists():
        return None

    bounds = _ctags_function_bounds(
        str(filepath), func_def.name, func_def.line
    )
    if bounds is None:
        return None

    start_line, end_line = bounds
    lines = filepath.read_text(errors="replace").splitlines()
    # Clamp to file length
    start_idx = max(start_line - 1, 0)
    end_idx = min(end_line, len(lines))
    source = "\n".join(lines[start_idx:end_idx])

    return FunctionBody(
        file=func_def.file,
        start_line=start_line,
        end_line=end_line,
        source=source,
    )


def list_symbols(project_dir: str) -> list[str]:
    """Use `global -c` to list all completions (symbol names)."""
    global_bin = _check_global()
    root = Path(project_dir).resolve()
    result = subprocess.run(
        [global_bin, "-c", ""],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    return [s for s in result.stdout.strip().splitlines() if s]
