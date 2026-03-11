---
name: path
description: Find call paths between two functions using BFS over the call graph. Use this skill whenever the user wants to trace execution flow, verify reachability between functions, find call chains for security auditing (e.g. "can user input reach this sink?"), debug a crash, or understand how one function eventually leads to another. Invoke even when they say "trace", "how does X get to Y", "is Y reachable", "what's the execution path", or "find the call chain".
compatibility: Requires GNU Global and Universal Ctags (auto-ensures index and graph)
---

# Call Path Finding

Find all call paths from a source function to a target function using breadth-first search. This is the go-to skill for reachability questions — it automatically builds the index and call graph if they don't already exist.

## When to use

Use this skill when the user asks:
- "Can function X reach function Y?" / "Is Y reachable from X?"
- "What are the call paths from X to Y?" / "How many ways can X reach Y?"
- "How does function X eventually call function Y?"
- "Trace the execution from X to Y"
- "Can user input reach `strcpy`?" / security reachability questions
- "What's the call stack that leads to Y?"

## How to invoke

**Invocation:** Use the `claudit` CLI only. Do not run `python -m claudit.skills.path`.

```bash
claudit path find <source> <target> <project_dir> [--language c|java|python] [--max-depth 10] [--overrides path.json]
```

- `--max-depth N` (default 10): controls BFS depth — shorter = faster but may miss longer paths; increase if you suspect the path exists but isn't being found
- `--overrides path.json`: supply extra edges for dynamic dispatch (Java interfaces, C function pointers) that static analysis misses
- `--language`: auto-detected if omitted

```python
from claudit.skills.path import find

result = find("/path/to/project", "main", "vulnerable_func", max_depth=10)
```

## Output format

```json
{
  "source": "main",
  "target": "vulnerable_func",
  "paths": [
    {
      "hops": [
        {"function": "main", "file": "main.c", "line": 42, "snippet": "process_input(buf);"},
        {"function": "process_input", "file": "input.c", "line": 15, "snippet": "parse_data(raw);"},
        {"function": "vulnerable_func", "file": "vuln.c", "line": 3, "snippet": "void vulnerable_func(char *p) {"}
      ],
      "length": 3
    }
  ],
  "path_count": 1,
  "cache_used": false
}
```

## Notes

- Auto-builds the call graph and index if they don't exist.
- Empty `paths` array means no reachable path within the depth limit.
- Use `--max-depth` to control how deep the BFS searches.

## Limitations

- GNU Global can miss edges across Java interface -> implementation (e.g. a call in the impl is not attributed to the interface). If `path find` returns 0 paths, the path may still exist; verify by reading source and/or using `claudit graph callees` and `claudit graph callers`.

## When path find returns no paths

1. Run `claudit path find <src> <tgt> <dir>` first.
2. If 0 paths, run `claudit graph callees <src> <dir>` to see direct callees.
3. Run `claudit graph callers <tgt> <dir>` to see callers of the target.
4. Read source of promising intermediate functions to find the missing edge.
5. Once the chain is confirmed, pass the hop list to `claudit highlight path ... --project-dir <dir>`.
