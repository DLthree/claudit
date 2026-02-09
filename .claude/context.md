# claudit - Code Auditing Skills for Claude Code

## Overview

claudit is a Python library and CLI tool that provides code auditing capabilities for Claude Code. It ships four composable skills — **index**, **graph**, **path**, and **highlight** — for analyzing call relationships in large codebases using GNU Global indexing and Pygments-based static analysis.

## Tech Stack

- **Language:** Python 3.10+
- **Build system:** setuptools (configured in `pyproject.toml`)
- **Test framework:** pytest with pytest-cov
- **Key dependency:** Pygments >= 2.17
- **System dependencies:** GNU Global (`gtags`/`global`), Universal Ctags, ripgrep (optional, for C function pointer resolution)

## Project Layout

```
src/claudit/
  cli.py                          # CLI entry point — two-level subcommand dispatch
  errors.py                       # Shared exception classes
  lang.py                         # detect_language, LEXER_MAP, load_overrides
  skills/
    index/
      __init__.py                 # Public API: create, list_symbols, get_body, lookup
      indexer.py                  # GNU Global + ctags wrapper
      cli.py                     # CLI registration for `claudit index`
    graph/
      __init__.py                 # Public API: build, show, callees, callers
      callgraph.py               # Pygments-based call graph construction
      cache.py                   # GTAGS mtime-keyed caching layer
      cli.py                     # CLI registration for `claudit graph`
    path/
      __init__.py                 # Public API: find
      pathfinder.py              # BFS path finding with annotation
      cli.py                     # CLI registration for `claudit path`
    highlight/
      __init__.py                 # Public API: highlight_path, highlight_function
      renderer.py                # Pygments-based highlighting + annotations
      cli.py                     # CLI registration for `claudit highlight`
tests/
  conftest.py                    # Shared fixtures (c_project, python_project)
  test_cli.py                    # CLI dispatch tests
  test_lang.py                   # detect_language, load_overrides, LEXER_MAP
  test_index/                    # test_indexer.py, test_api.py
  test_graph/                    # test_callgraph.py, test_cache.py, test_api.py
  test_path/                     # test_pathfinder.py
  test_highlight/                # test_renderer.py
```

## CLI Commands

```bash
claudit index create <project_dir> [--force]
claudit index list-symbols <project_dir>
claudit index get-body <function> <project_dir> [--language c|java|python]
claudit index lookup <symbol> <project_dir> [--kind definitions|references|both]

claudit graph build <project_dir> [--language ...] [--overrides path.json] [--force]
claudit graph show <project_dir>
claudit graph callees <function> <project_dir>
claudit graph callers <function> <project_dir>

claudit path find <source> <target> <project_dir> [--max-depth 10] [--language ...]

claudit highlight path <func1> <func2> ... --project-dir <dir> [--style monokai]
claudit highlight function <func> --project-dir <dir>
```

## Python API

```python
from claudit.skills.index import create, list_symbols, get_body, lookup
from claudit.skills.graph import build, show, callees, callers
from claudit.skills.path import find
from claudit.skills.highlight import highlight_path, highlight_function
```

All functions return plain dicts (JSON-serializable).

## Development Commands

```bash
pip install -e ".[dev]"    # Install with dev dependencies
pytest --no-cov            # Run tests (fast, no coverage)
pytest                     # Run tests with coverage
```

## Key Patterns

- **Shared modules**: `errors.py` (exceptions), `lang.py` (language detection, LEXER_MAP, load_overrides)
- **Each skill**: `__init__.py` (public API), implementation module, `cli.py`
- **Dataclasses**: `FunctionDef`, `FunctionBody`, `Hop`, `CallPath`
- **Graph representation**: `dict[str, list[str]]` mapping callers to callees
- **Dependency chain**: index -> graph -> path (each skill auto-ensures prerequisites by default)

## Rules for Making Changes

1. **Always update `.claude/` when changing architecture.** Any change to the project structure, CLI commands, Python API, or skill boundaries MUST include corresponding updates to `.claude/context.md` and the relevant `.claude/skills/*.md` files. These are the source of truth for how Claude interacts with the project.

2. **No backward-compat shims.** When moving code, delete the old location. Do not leave re-export shims behind. Update all imports and patch targets in tests to point to the canonical location.

3. **Tests should be realistic.** Prefer testing pure functions directly without mocking. Only mock at the subprocess boundary (global, gtags, ctags, rg). Never mock private implementation details just to make tests pass — if a test requires patching internal aliases, the code structure is wrong.

4. **One source of truth for shared code.** Shared constants (LEXER_MAP), utilities (load_overrides, detect_language), and exceptions all live in top-level modules (`lang.py`, `errors.py`). Skills import from there — never duplicate.
