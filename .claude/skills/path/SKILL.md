---
name: path
description: Find call paths between two functions using BFS over the call graph. Use when the user asks if function X can reach Y, what paths exist from X to Y, or how X eventually calls Y.
---

# Call Path Finding

Find call paths between two functions using BFS over the call graph.

## When to use

Use this skill when the user asks:
- "Can function X reach function Y?"
- "What are the call paths from X to Y?"
- "How does function X eventually call function Y?"
- "Is function Y reachable from function X?"

## How to invoke

**Invocation:** Use the `claudit` CLI only. Do not run `python -m claudit.skills.path`.

```bash
claudit path find <source> <target> <project_dir> [--language c|java|python] [--max-depth 10] [--overrides path.json]
```

- `--language` and `--max-depth N` (default 10) apply to `claudit path find` only.

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

- GNU Global can miss edges across Java interface → implementation (e.g. a call in the impl is not attributed to the interface). If `path find` returns 0 paths, the path may still exist; verify by reading source and/or using `claudit graph callees` and `claudit graph callers`.

## When path find returns no paths

1. Run `claudit path find <src> <tgt> <dir>` first.
2. If 0 paths, run `claudit graph callees <src> <dir>` to see direct callees.
3. Run `claudit graph callers <tgt> <dir>` to see callers of the target.
4. Read source of promising intermediate functions to find the missing edge.
5. Once the chain is confirmed, pass the hop list to `claudit highlight path ... --project-dir <dir>`.
