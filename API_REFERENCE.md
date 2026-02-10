# claudit API Reference

## Python API (primary)

Invocation is primarily via Claude Code using these entry points. All functions return plain dicts or dataclasses (JSON-serializable where applicable).

```python
from claudit.skills.index import create, list_symbols, get_body, lookup
from claudit.skills.graph import build, show, callees, callers
from claudit.skills.path import find
from claudit.skills.highlight import highlight_path, highlight_function
from claudit.skills.harness import (
    extract_function,
    extract_functions,
    extract_file,
    list_functions_in_file,
    analyze_dependencies,
    get_function_signature,
    get_function_callees,
)
# Harness types: ExtractedFunction, DependencySet, FunctionSignature, Parameter
```

## CLI (optional)

For debugging or scripting. Primary use is from Claude via the Python API above. Use the `claudit` CLI only; do not run `python -m claudit.skills.<name>` — those are packages, not runnable modules.

```bash
claudit index create <project_dir> [--force]
claudit index list-symbols <project_dir>
claudit index get-body <function> <project_dir> [--language c|java|python]
claudit index lookup <symbol> <project_dir> [--kind definitions|references|both]

claudit graph build <project_dir> [--language ...] [--overrides path.json] [--force]
claudit graph show <project_dir>
claudit graph callees <function> <project_dir>
claudit graph callers <function> <project_dir>

claudit path find <source> <target> <project_dir> [--max-depth 10] [--language ...]

claudit highlight path <func1> <func2> ... --project-dir <dir> [--style monokai]
claudit highlight function <func> --project-dir <dir>

claudit harness extract (--functions <names> | --file <path>) <project_dir> [--language c|java|python]
claudit harness list-functions <project_dir> --file <path>
claudit harness analyze-deps <project_dir> --functions <names> [--depth N]
claudit harness get-signature <project_dir> --function <name> [--language c|java|python]
```
