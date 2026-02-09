"""Backward-compatibility shim – delegates to claudit.skills.path.pathfinder."""

from claudit.skills.path.pathfinder import (  # noqa: F401
    Hop,
    CallPath,
    find_all_paths,
    annotate_path,
    _read_line,
)
