"""GNU Global indexing interface.

Handles running gtags, querying definitions/references, and extracting
function body bounds from the indexed project.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


class GlobalNotFoundError(Exception):
    """Raised when GNU Global is not installed."""

    def __init__(self) -> None:
        super().__init__(
            "GNU Global (gtags/global) is not installed.\n"
            "Install it with:\n"
            "  Ubuntu/Debian: sudo apt-get install global\n"
            "  macOS:         brew install global\n"
            "  Fedora:        sudo dnf install global"
        )


class IndexingError(Exception):
    """Raised when gtags indexing fails."""


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


def get_function_body(
    func_def: FunctionDef,
    project_dir: str,
    language: str,
) -> FunctionBody | None:
    """Extract the source of a function body given its definition location.

    Uses brace/indent counting to find body bounds.
    """
    root = Path(project_dir).resolve()
    filepath = root / func_def.file
    if not filepath.exists():
        return None

    lines = filepath.read_text(errors="replace").splitlines()
    start = func_def.line - 1  # 0-indexed

    if language in ("c", "java"):
        return _extract_brace_body(lines, start, func_def.file)
    elif language == "python":
        return _extract_indent_body(lines, start, func_def.file)
    return None


def _extract_brace_body(
    lines: list[str], start: int, filepath: str
) -> FunctionBody:
    """Extract body for brace-delimited languages (C, Java)."""
    depth = 0
    found_open = False
    end = start

    for i in range(start, len(lines)):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
                found_open = True
            elif ch == "}":
                depth -= 1
                if found_open and depth == 0:
                    end = i
                    source = "\n".join(lines[start : end + 1])
                    return FunctionBody(
                        file=filepath,
                        start_line=start + 1,
                        end_line=end + 1,
                        source=source,
                    )

    # If we never found a matching brace, return from start to EOF
    end = len(lines) - 1
    source = "\n".join(lines[start : end + 1])
    return FunctionBody(
        file=filepath,
        start_line=start + 1,
        end_line=end + 1,
        source=source,
    )


def _extract_indent_body(
    lines: list[str], start: int, filepath: str
) -> FunctionBody:
    """Extract body for indent-delimited languages (Python)."""
    if start >= len(lines):
        return FunctionBody(
            file=filepath, start_line=start + 1, end_line=start + 1, source=""
        )

    # Find the indent of the def line
    def_line = lines[start]
    def_indent = len(def_line) - len(def_line.lstrip())

    # Skip decorator lines above if start points at a decorator
    # Find body start (first line after the def with colon)
    body_start = start + 1

    # Handle multi-line def statements
    paren_depth = 0
    for i in range(start, len(lines)):
        paren_depth += lines[i].count("(") - lines[i].count(")")
        if paren_depth <= 0 and ":" in lines[i]:
            body_start = i + 1
            break

    end = body_start
    for i in range(body_start, len(lines)):
        stripped = lines[i].strip()
        if stripped == "" or stripped.startswith("#"):
            end = i
            continue
        current_indent = len(lines[i]) - len(lines[i].lstrip())
        if current_indent <= def_indent:
            break
        end = i

    source = "\n".join(lines[start : end + 1])
    return FunctionBody(
        file=filepath,
        start_line=start + 1,
        end_line=end + 1,
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
