---
name: results
description: Convert a call path into Results Format JSON without syntax highlighting. Use when the user wants a structured result set from a call path (for the VS Code Manual Result Set Extension) but does NOT want color-annotated source code. Invoke when the user says "output results for this path", "give me the results format", "export as results", "convert path to results", or "generate a result set" — and is NOT asking for syntax highlighting or source visualization.
---

# Results Format Output

Convert a call path into Results Format JSON — the same schema used by `/highlight`, but without syntax highlighting. Only include `color` if the user explicitly specifies one.

## Workflow

1. **Get the path** — from `claudit path find` output (`hops[].function` values in order), or a manually confirmed chain.
2. **Resolve each hop** — for each function in the path, determine the file, line number, and column range where the function is **defined**, and where it **calls** the next function in the chain. Use `claudit highlight path` output as a reference for accurate positions when available; otherwise derive from `claudit index get-body`.
3. **Emit Results Format JSON** — one result entry per definition span and per call-site span. Omit `color` unless the user specified one.

## Output format

Conforms to the Results Format schema: top-level `metadata` and `results` array.

- **Definition span**: file + line + columns where the function is defined.
- **Call-site span**: file + line + columns where the next function in the path is called.
- Each hop shares one `color` (if provided by user). **Omit the `color` field entirely when no color is specified.**

```json
{
  "metadata": {
    "author": "claudit results",
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
      "function": "main"
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
      "function": "main"
    }
  ]
}
```

When the user specifies a color, add `"color": "rgba(r, g, b, 0.3)"` to every result entry for that hop.

## Notes

- **No highlighting** — never call `claudit highlight`. Only produce JSON.
- **Color is optional** — include `color` only when the user explicitly provides one. When omitted, the field must not appear in the output at all.
