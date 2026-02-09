"""Highlight skill – syntax-highlighted source with annotations.

Public API
----------
- highlight_path(project_dir, path, *, language=None, style="monokai") -> dict
- highlight_function(project_dir, function, *, language=None, style="monokai") -> dict | None
"""

from claudit.skills.highlight.renderer import (  # noqa: F401
    highlight_path,
    highlight_function,
)
