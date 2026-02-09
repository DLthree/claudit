# claudit - Code Auditing Skills for Claude Code

## Overview

claudit is a Python library and CLI tool that provides code auditing capabilities for Claude Code. Currently it ships a single skill — **reachability analysis** — which finds call paths between two functions in large, heterogeneous codebases using GNU Global indexing and Pygments-based static analysis.

## Tech Stack

- **Language:** Python 3.10+
- **Build system:** setuptools (configured in `pyproject.toml`)
- **Test framework:** pytest with pytest-cov
- **Key dependency:** Pygments >= 2.17
- **System dependencies:** GNU Global (`gtags`/`global`), Universal Ctags, ripgrep (optional, for C function pointer resolution)

## Project Layout

```
src/claudit/
  cli.py                          # CLI entry point (claudit command)
  skills/
    reachability/
      core.py                     # Orchestration — find_reachability()
      indexer.py                  # GNU Global + ctags wrapper
      callgraph.py               # Pygments-based call graph construction
      cache.py                   # GTAGS mtime-keyed caching layer
      pathfinder.py              # BFS path finding with annotation
tests/
  test_cli.py                    # CLI argument parsing tests
  test_reachability/
    test_indexer.py
    test_callgraph.py
    test_cache.py
    test_pathfinder.py
```

## Entry Points

**CLI:**
```bash
claudit reachability <source> <target> <project_dir> [--language c|java|python] [--max-depth 10] [--overrides path.json]
```

**Python API:**
```python
from claudit.skills.reachability import find_reachability
result = find_reachability(source, target, project_dir, language, max_depth, overrides_path)
```

The CLI entry point is registered as `claudit = "claudit.cli:main"` in `pyproject.toml`.

## Architecture

The reachability skill follows a layered design:

1. **CLI** (`cli.py`) — parses arguments, dispatches to the orchestrator
2. **Orchestrator** (`core.py`) — coordinates indexing, caching, graph building, and path finding
3. **Indexer** (`indexer.py`) — wraps GNU Global and Universal Ctags; extracts function definitions and bodies
4. **Call Graph Builder** (`callgraph.py`) — tokenizes function bodies with Pygments to build caller→callee edges; handles C function pointers via ripgrep
5. **Cache** (`cache.py`) — memoizes call graphs keyed on a hash of the project path + GTAGS mtime
6. **Pathfinder** (`pathfinder.py`) — BFS traversal to find all paths up to a configurable max depth; annotates hops with source locations

Supported analysis languages: **C**, **Java**, **Python** (one language per analysis run).

## Development Commands

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests (includes coverage report)
pytest

# Run a specific test file
pytest tests/test_reachability/test_callgraph.py
```

## Key Patterns & Conventions

- **Type hints** throughout, using Python 3.10+ syntax with `from __future__ import annotations`
- **Dataclasses** for value objects: `FunctionDef`, `FunctionBody`, `Hop`, `CallPath`
- **Custom exceptions**: `GlobalNotFoundError`, `CtagsNotFoundError`, `IndexingError`
- **Private helpers** prefixed with `_` (e.g., `_project_hash`, `_cache_dir`)
- **Subprocess calls** for external tools with robust error handling
- **Graph representation**: `dict[str, list[str]]` mapping callers to callees

## CI/CD

GitHub Actions workflow (`.github/workflows/coverage.yml`) runs on pushes to `main`:
- Ubuntu runner with Python 3.11
- Installs `universal-ctags` as system dependency
- Runs `pytest` and generates a coverage badge
- Auto-commits the badge back to the repo

## Limitations & Notes

- Analysis is single-language per run
- Requires GNU Global and Universal Ctags installed on the system
- Call graph is built from lexical tokens (Pygments), not a full AST — may include false positives from comments/strings in edge cases
- Manual override files (JSON) can supplement the call graph where static analysis falls short
