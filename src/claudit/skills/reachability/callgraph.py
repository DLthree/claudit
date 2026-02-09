"""Backward-compatibility shim – delegates to claudit.skills.graph.callgraph."""

from claudit.skills.graph.callgraph import (  # noqa: F401
    build_call_graph,
    _callees_of,
    _extract_calls_from_source,
    _resolve_c_function_pointers,
    _find_enclosing_function,
    LEXER_MAP,
)

from claudit.lang import detect_language  # noqa: F401

# Re-export indexer types for backward compat
from claudit.skills.index.indexer import FunctionDef, FunctionBody  # noqa: F401
