---
name: index
description: Manage GNU Global indexes for code analysis. Use when the user asks to index a project, list symbols, find where a function is defined, show function source, or find references to a symbol.
---

# Index Management

Manage GNU Global indexes for code analysis.

## When to use

Use this skill when the user asks:
- "Index this project" / "Create an index"
- "What symbols are in this project?"
- "Where is function X defined?"
- "Show me the source of function X"
- "What references function X?"

## How to invoke

```bash
claudit index create <project_dir> [--force]
claudit index list-symbols <project_dir>
claudit index get-body <function> <project_dir> [--language c|java|python]
claudit index lookup <symbol> <project_dir> [--kind definitions|references|both]
```

```python
from claudit.skills.index import create, list_symbols, get_body, lookup
```

## Prerequisites

- GNU Global (`gtags`/`global`) must be installed.
- Universal Ctags for `get-body` (function body extraction).
