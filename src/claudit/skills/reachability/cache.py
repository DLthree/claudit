"""Backward-compatibility shim – delegates to claudit.skills.graph.cache."""

from claudit.skills.graph.cache import (  # noqa: F401
    load_call_graph,
    save_call_graph,
    load_global_results,
    save_global_results,
    _project_hash,
    _cache_dir,
    _cache_key,
)
