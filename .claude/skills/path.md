# Call Path Finding

Find call paths between two functions using BFS over the call graph.

## When to use

Use this skill when the user asks:
- "Can function X reach function Y?"
- "What are the call paths from X to Y?"
- "How does function X eventually call function Y?"
- "Is function Y reachable from function X?"

## How to invoke

```bash
claudit path find <source> <target> <project_dir> [--language c|java|python] [--max-depth 10] [--overrides path.json]
```

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
