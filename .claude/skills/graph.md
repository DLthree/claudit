# Call Graph Operations

Build and query call graphs showing which functions call which.

## When to use

Use this skill when the user asks:
- "Build a call graph for this project"
- "What does function X call?" / "What are the callees of X?"
- "What calls function X?" / "What are the callers of X?"
- "Show me the full call graph"

## How to invoke

```bash
claudit graph build <project_dir> [--language c|java|python] [--overrides path.json] [--force]
claudit graph show <project_dir>
claudit graph callees <function> <project_dir>
claudit graph callers <function> <project_dir>
```

```python
from claudit.skills.graph import build, show, callees, callers
```

## Notes

- Building the call graph is the most expensive operation — it indexes every symbol, extracts function bodies, and tokenizes them with Pygments.
- Results are cached in `.cache/` keyed on GTAGS mtime. Use `--force` to rebuild.
- Manual overrides JSON can supplement static analysis for dynamic dispatch, callbacks, etc.
