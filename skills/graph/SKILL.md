---
name: graph
description: Build and query call graphs showing which functions call which. Use this skill whenever the user wants to understand call relationships in a codebase — who calls a function, what a function calls, whether there are circular dependencies, or how data flows between functions. Invoke this even when the user doesn't say "call graph" explicitly, such as "trace this function", "what uses X", "find all callers", or as a fallback when path finding returns 0 paths.
compatibility: Requires GNU Global; optional ripgrep for C function pointer resolution
---

# Call Graph Operations

The call graph lets you answer "who calls what" questions without reading every file. It also serves as the fallback tool when `path find` returns 0 paths — use `graph callees` and `graph callers` together to manually reconstruct a path through source inspection.

## When to use

Use this skill when the user asks:
- "Build a call graph for this project"
- "What does function X call?" / "What are the callees of X?"
- "What calls function X?" / "What are the callers of X?" / "Who uses X?"
- "Show me the full call graph" / "Show call relationships"
- "Trace data flow from X" / "Find all uses of X"
- As a fallback when `claudit path find` returns 0 paths (see the path skill for the exact workflow)

## How to invoke

**Invocation:** Use the `claudit` CLI only. Do not run `python -m claudit.skills.graph`.

```bash
claudit graph build <project_dir> [--language c|java|python] [--overrides path.json] [--force]
claudit graph show <project_dir>
claudit graph callees <function> <project_dir>
claudit graph callers <function> <project_dir>
```

**Subcommand syntax:** Use `callees` and `callers` as subcommands, not flags.
- Wrong: `claudit graph query --callees <func>` (no `graph query` subcommand exists)
- Correct: `claudit graph callees <func> <dir>`, `claudit graph callers <func> <dir>`

**Flag placement:** `--language` is only accepted by `graph build`. Do NOT pass `--language` to `graph callees` or `graph callers` — those commands infer language from the cached index automatically.

```python
from claudit.skills.graph import build, show, callees, callers
```

## Cost and caching

Building the call graph is the most expensive claudit operation — it tokenizes every function body with Pygments to extract call edges. Results are cached in `.cache/` keyed on GTAGS mtime, so subsequent calls are fast. Use `--force` to rebuild after code changes.

## Manual overrides

Static analysis misses dynamic dispatch (C function pointers, Java interfaces, virtual methods). Use `--overrides path.json` to supply edges that the static analyzer can't see. This is especially useful for Java Spring applications where the interface → implementation relationship is implicit.

## Known limitations

GNU Global misses Java interface → implementation edges. For example, if `processRequest` is declared in an interface and the actual call to `executeQuery` lives in the implementation class, that edge won't appear in the graph. This is why `path find` may return 0 paths in Java projects even when a path exists.

**Workaround:** Use `claudit graph callees <interface_method>` and `claudit graph callers <target>` to find what edges exist, then read the implementation class source to confirm the missing edge manually.
