# Code Reachability Analysis

Find call paths between functions in large heterogeneous codebases using GNU Global + static analysis.

## When to use

Use this skill when the user asks:
- "Can function X reach function Y?"
- "What are the call paths from X to Y?"
- "How does function X eventually call function Y?"
- "Is function Y reachable from function X?"
- Any question about function call chains, call graphs, or code reachability.

## Supported languages

C, Java, Python (one at a time, no cross-language analysis).

## Prerequisites

- GNU Global (`gtags`/`global`) must be installed on the system.
- Pygments (installed as a dependency of claudit).
- ripgrep (`rg`) is optional but improves C function pointer resolution.

## How to invoke

Run the `claudit reachability` command:

```bash
claudit reachability <source_function> <target_function> <project_dir> [--language c|java|python] [--max-depth N] [--overrides path/to/overrides.json]
```

Or call the Python API directly:

```python
from claudit.skills.reachability import find_reachability

result = find_reachability(
    source="main",
    target="vulnerable_func",
    project_dir="/path/to/project",
    language="c",        # optional, auto-detected
    max_depth=10,        # optional, default 10
    overrides_path=None, # optional
)
```

## Output format

```json
{
  "paths": [
    {
      "hops": [
        {
          "function": "main",
          "file": "src/main.c",
          "line": 42,
          "snippet": "process_input(buf);"
        },
        {
          "function": "process_input",
          "file": "src/input.c",
          "line": 15,
          "snippet": "parse_data(raw);"
        },
        {
          "function": "parse_data",
          "file": "src/parser.c",
          "line": 88,
          "snippet": "vulnerable_func(ptr);"
        },
        {
          "function": "vulnerable_func",
          "file": "src/vuln.c",
          "line": 3,
          "snippet": "void vulnerable_func(char *p) {"
        }
      ]
    }
  ],
  "cache_used": false
}
```

## Interpreting results

- **paths**: Array of all discovered call paths from source to target. Each path contains an ordered list of hops.
- **hops**: Each hop shows the function name, its file location, line number, and a source snippet.
- **cache_used**: Whether a cached call graph was used (true) or a fresh graph was built (false).
- Empty `paths` array means no reachable path was found within the depth limit.

## Manual overrides

For cases where static analysis misses edges (e.g., dynamic dispatch, callbacks registered at runtime), create an overrides JSON file:

```json
{
  "dispatch_handler": ["concrete_handler_a", "concrete_handler_b"],
  "register_callback": ["my_callback"]
}
```

Pass it with `--overrides path/to/overrides.json`.

## Caching

- Call graphs are cached in `.cache/` at the project root.
- Cache is keyed on the project path and GTAGS modification time.
- Re-running `gtags` (or deleting GTAGS) invalidates the cache automatically.

## Limitations

- Single language per analysis run (no cross-language call tracking).
- C function pointer resolution is best-effort via pattern matching.
- Macro-expanded calls may be missed if GNU Global doesn't index them.
- Virtual method dispatch in Java is resolved to all possible targets (over-approximation).
