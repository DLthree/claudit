---
name: index
description: Manage GNU Global indexes for code analysis. Use this skill whenever the user wants to explore what functions exist in a codebase, find where a symbol is defined or referenced, read source for a specific function, or needs an index for any code analysis — even if they just say "index the project", "find function X", "what's in this codebase", or are about to do call graph or path analysis. Always index first when starting work on a new project.
compatibility: Requires GNU Global (gtags/global) and Universal Ctags
---

# Index Management

The index is the foundation for all other claudit skills (graph, path, highlight, harness all depend on it). Building the index is fast and non-destructive — always safe to run.

## When to use

Use this skill when the user asks:
- "Index this project" / "Create an index" / "Set up the project"
- "What symbols / functions are in this project?"
- "Where is function X defined?" / "Show me the source of function X"
- "What references function X?" / "What calls function X?"
- Any time you're about to use `graph`, `path`, `highlight`, or `harness` on a project that hasn't been indexed yet

Other skills (`graph`, `path`, `harness`) call `claudit index create` automatically via `auto_index=True`. You only need to invoke this skill explicitly when the user asks about symbols/definitions directly, or to force a re-index after code changes.

## How to invoke

**Invocation:** Use the `claudit` CLI only. Do not run `python -m claudit.skills.index`.

```bash
claudit index create <project_dir> [--force]
claudit index list-symbols <project_dir>
claudit index get-body <function> <project_dir> [--language c|java|python]
claudit index lookup <symbol> <project_dir> [--kind definitions|references|both]
```

```python
from claudit.skills.index import create, list_symbols, get_body, lookup
```

## Output format

`get-body` returns the full source of the function. `lookup` returns definitions and/or references:

```json
{
  "symbol": "authenticate_user",
  "definitions": [
    {"file": "src/auth.c", "line": 42, "kind": "function"}
  ],
  "references": [
    {"file": "src/main.c", "line": 15},
    {"file": "src/admin.c", "line": 88}
  ]
}
```

## Prerequisites

- GNU Global (`gtags`/`global`) must be installed.
- Universal Ctags for `get-body` (function body extraction).
- Use `--force` to rebuild the index after code changes — the other skills won't auto-detect stale indexes.
