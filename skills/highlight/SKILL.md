---
name: highlight
description: Syntax-highlight source code with per-hop color annotations for call path visualization. Use this skill after finding a call path (with the path skill), when the user wants to visually trace code execution, see highlighted source for a function, or produce output for the VS Code Manual Result Set Extension. Invoke whenever the user says "show me the code", "highlight the path", "visualize the call chain", "annotate the source", or after you've identified a call path and want to present it clearly.
compatibility: Requires GNU Global, Universal Ctags, and Pygments
---

# Source Highlighting

Produce color-annotated source code highlighting every definition and call site along a call chain. The output is designed for the VS Code Manual Result Set Extension — paste it in and each hop lights up in a distinct color, making the execution flow immediately visible.

## When to use

Use this skill when the user asks:
- "Highlight the code along this call path"
- "Show me the source of function X with syntax highlighting"
- "Visualize the call chain from X to Y" / "Annotate the path"
- "Show me where these functions are defined and called"
- **After using the `path` skill** to find a call chain — always offer to highlight the result so the user can see it visually

## How to invoke

**Invocation:** Use the `claudit` CLI only. Do not run `python -m claudit.skills.highlight`.

```bash
# Highlight an entire call chain (pass the functions in order)
claudit highlight path <func1> <func2> <func3> --project-dir <dir> [--style monokai]

# Highlight a single function's source
claudit highlight function <func> --project-dir <dir> [--language c|java|python]
```

The hop list for `highlight path` comes from `claudit path find` output (use the `hops[].function` values in order), or from a manually confirmed chain when auto-discovery returns 0 paths (see path skill "When path find returns no paths" workflow).

Available `--style` values include: `monokai`, `solarized-dark`, `github-dark`, `friendly` (default).

```python
from claudit.skills.highlight import highlight_path, highlight_function

# Highlight an entire call path
result = highlight_path("/project", ["main", "process", "target"], language="c")

# Highlight a single function
result = highlight_function("/project", "main", language="c")
```

## Output format (highlight path)

For **path**, the output conforms to the [Results Format](dev/RESULTS_FORMAT.md): top-level `metadata` and `results` array. Each entry in the call chain is represented by **only** the definition span and the call-site span(s)---not every line in the function body.

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

- **Path output** follows the Results Format (`dev/RESULTS_FORMAT.md`) — load it directly into the VS Code Manual Result Set Extension. Only definition and call-site spans are emitted, not entire function bodies. This keeps the output focused on what matters for tracing the path.
- **Each hop gets a distinct color** from a 10-color RGBA palette. The definition and call-site for each hop share the same color, making it easy to see "this pink highlight is all about `processInput`".
- **Single function** (`highlight function`): returns raw source plus Pygments `highlighted_html` for the full function body — useful for displaying a single function without a path context.
