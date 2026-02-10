# claudit - Code Auditing Skills for Claude Code

## Overview

claudit is a Python library that provides code auditing capabilities **invoked from inside Claude Code**. The agent uses the Python API (skill entry points); the CLI is optional (debugging/scripting). It ships five composable skills — **index**, **graph**, **path**, **highlight**, and **harness** — for analyzing call relationships in large codebases using GNU Global indexing and Pygments-based static analysis. The harness skill adds extraction and dependency analysis for building test harnesses (LLM-guided).

## Tech Stack

- **Language:** Python 3.10+
- **Build system:** setuptools (configured in `pyproject.toml`)
- **Test framework:** pytest with pytest-cov
- **Key dependency:** Pygments >= 2.17
- **System dependencies:** GNU Global (`gtags`/`global`), Universal Ctags, ripgrep (optional, for C function pointer resolution)

## Project Layout

```
src/claudit/
  errors.py                       # Shared exception classes
  lang.py                         # detect_language, LEXER_MAP, load_overrides
  skills/
    index/
      indexer.py                  # GNU Global + ctags wrapper
    graph/
      callgraph.py                # Pygments-based call graph construction
      cache.py                    # GTAGS mtime-keyed caching layer
    path/
      pathfinder.py               # BFS path finding with annotation
    highlight/
      renderer.py                 # Pygments-based highlighting + annotations
    harness/
      extractor.py                # Extraction
      dependency_analyzer.py      # Dependency analysis
      signature_extractor.py      # Signatures
tests/
  conftest.py                    # Shared fixtures (c_project, python_project)
  test_cli.py                    # CLI dispatch tests
  test_lang.py                   # detect_language, load_overrides, LEXER_MAP
  test_index/                    # test_indexer.py, test_api.py
  test_graph/                    # test_callgraph.py, test_cache.py, test_api.py
  test_path/                     # test_pathfinder.py
  test_highlight/                # test_renderer.py
  test_harness/                  # test_api.py, test_signature.py
```

@API_REFERENCE.md

## Development Commands

```bash
pip install -e ".[dev]"    # Install with dev dependencies
pytest --no-cov            # Run tests (fast, no coverage)
pytest                     # Run tests with coverage
```

## Key Patterns

- **Shared modules**: `errors.py` (exceptions), `lang.py` (language detection, LEXER_MAP, load_overrides)
- **Each skill**: `__init__.py` (public API), implementation module(s), `cli.py`
- **Dataclasses**: `FunctionDef`, `FunctionBody`, `Hop`, `CallPath`; harness: `ExtractedFunction`, `DependencySet`, `FunctionSignature`, `Parameter`
- **Graph representation**: `dict[str, list[str]]` mapping callers to callees
- **Dependency chain**: index → graph → path (each skill auto-ensures prerequisites by default); harness uses index + graph

## Rules for Making Changes

1. **No backward-compat shims.** When moving code, delete the old location. Do not leave re-export shims behind. Update all imports and patch targets in tests to point to the canonical location.

2. **Tests should be realistic.** Prefer testing pure functions directly without mocking. Only mock at the subprocess boundary (global, gtags, ctags, rg). Never mock private implementation details just to make tests pass — if a test requires patching internal aliases, the code structure is wrong.

3. **One source of truth for shared code.** Shared constants (LEXER_MAP), utilities (load_overrides, detect_language), and exceptions all live in top-level modules (`lang.py`, `errors.py`). Skills import from there — never duplicate.
