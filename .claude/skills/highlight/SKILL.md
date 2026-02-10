---
name: highlight
description: Syntax-highlight source code with per-hop color annotations for call path visualization. Use when the user asks to highlight code along a call path, show highlighted source of a function, or visualize call chains.
---

# Source Highlighting

Syntax-highlighted source code with per-hop color annotations for call path visualization.

## When to use

Use this skill when the user asks:
- "Highlight the code along this call path"
- "Show me the source of function X with syntax highlighting"
- "Visualize the call chain from X to Y"

## How to invoke

**Invocation:** Use the `claudit` CLI only. Do not run `python -m claudit.skills.highlight`.

```bash
claudit highlight path <func1> <func2> <func3> --project-dir <dir> [--style monokai]
claudit highlight function <func> --project-dir <dir> [--language c|java|python]
```

The hop list for `highlight path` can come from `claudit path find` or from a manually confirmed chain when auto-discovery returns 0 paths (see path skill "When path find returns no paths" workflow).

```python
from claudit.skills.highlight import highlight_path, highlight_function

# Highlight an entire call path
result = highlight_path("/project", ["main", "process", "target"], language="c")

# Highlight a single function
result = highlight_function("/project", "main", language="c")
```

## Output format (highlight path)

For **path**, the output conforms to the [Results Format](dev/RESULTS_FORMAT.md): top-level `metadata` and `results` array. Each entry in the call chain is represented by **only** the definition span and the call-site span(s)—not every line in the function body.

- **Definition span**: the line and column range where the function is **defined** (e.g. the function name).
- **Call-site span**: for each hop except the last, the line and column range where the **next** function in the path is **called**.

Each hop shares one color (RGBA) for both its definition and its call-site result.

```json
{
  "metadata": {
    "author": "claudit highlight",
    "timestamp": "2025-02-09T12:00:00.000Z",
    "tool": "claudit",
    "version": "0.1.0"
  },
  "results": [
    {
      "ID": "1",
      "description": "definition of main",
      "notes": "Entry point: calls process()",
      "category": "Call path",
      "severity": "info",
      "filename": "main.c",
      "linenum": 1,
      "col_start": 6,
      "col_end": 9,
      "function": "main",
      "color": "rgba(255, 107, 107, 0.3)"
    },
    {
      "ID": "2",
      "description": "call to process",
      "notes": "Entry point: calls process()",
      "category": "Call path",
      "severity": "info",
      "filename": "main.c",
      "linenum": 5,
      "col_start": 5,
      "col_end": 12,
      "function": "main",
      "color": "rgba(255, 107, 107, 0.3)"
    }
  ]
}
```

## Notes

- Path output uses the Results Format so tools (e.g. VS Code Manual Result Set Extension) can consume it directly.
- Only call-chain locations (definitions and call sites) are emitted; full function bodies are not included.
- Each hop gets a distinct color from a 10-color palette; definition and call-site for that hop share the same color.
- For a single function, `highlight function` still returns raw source and Pygments `highlighted_html` for the full body.
