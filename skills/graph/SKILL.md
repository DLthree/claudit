---
name: graph
description: Build and query call graphs showing which functions call which. Use when the user asks to build a call graph, find callees or callers of a function, show the full call graph, check dependencies between functions, or answer "who calls X" / "what does X call".
compatibility: Requires GNU Global; optional ripgrep for C function pointer resolution
---

## How to invoke

**Invocation:** Use the `claudit` CLI only. Do not run `python -m claudit.skills.graph`.

```bash
claudit graph build <project_dir> [--language c|java|python] [--overrides path.json] [--force]
claudit graph show <project_dir>
claudit graph callees <function> <project_dir>
claudit graph callers <function> <project_dir>
```

**Subcommand syntax:** Use `callees` and `callers` as subcommands, not flags. Wrong: `claudit graph query --callees <func>` or `--callers <func>` (there is no `graph query` subcommand). Correct: `claudit graph callees <func> <dir>`, `claudit graph callers <func> <dir>`.

**Flags:** `--language` is accepted only by `graph build`. `graph callees` and `graph callers` do not accept `--language`; language is inferred from the cached index.

```python
from claudit.skills.graph import build, show, callees, callers
```

## Notes

- Building the call graph is the most expensive operation — it indexes every symbol, extracts function bodies, and tokenizes them with Pygments.
- Results are cached in `.cache/` keyed on GTAGS mtime. Use `--force` to rebuild.
- Manual overrides JSON can supplement static analysis for dynamic dispatch, callbacks, etc.
- When path finding returns 0 paths (e.g. due to Java interface/impl or other missing edges), use `graph callees` and `graph callers` plus manual source inspection as in the path skill's "When path find returns no paths" workflow.
