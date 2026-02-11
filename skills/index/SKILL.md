---
name: index
description: Manage GNU Global indexes for code analysis. Use when the user asks to index a project, list symbols, find where a function is defined, show function source, find references to a symbol, look up a symbol, or answer "what functions exist in this project".
compatibility: Requires GNU Global (gtags/global) and Universal Ctags
---

## How to invoke

**Invocation:** Use the `claudit` CLI only. Do not run `python -m claudit.skills.index`.

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
