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

```bash
claudit highlight path <func1> <func2> <func3> --project-dir <dir> [--style monokai]
claudit highlight function <func> --project-dir <dir> [--language c|java|python]
```

```python
from claudit.skills.highlight import highlight_path, highlight_function

# Highlight an entire call path
result = highlight_path("/project", ["main", "process", "target"], language="c")

# Highlight a single function
result = highlight_function("/project", "main", language="c")
```

## Output format (highlight path)

```json
{
  "highlights": [
    {
      "function": "main",
      "file": "main.c",
      "start_line": 1,
      "end_line": 10,
      "source": "...",
      "highlighted_html": "<span ...>...</span>",
      "color": "#FF6B6B",
      "hop_index": 0,
      "note": "Entry point: calls process()",
      "call_site": {"line": 5, "callee": "process", "snippet": "    process(buf);"}
    }
  ],
  "style": "monokai",
  "path_length": 3
}
```

## Notes

- Each hop in the path gets a unique color from a 10-color palette.
- `call_site` shows where in the function body the next hop is called.
- `highlighted_html` uses Pygments HTML formatting (nowrap mode).
