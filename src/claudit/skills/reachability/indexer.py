"""Backward-compatibility shim – delegates to claudit.skills.index.indexer."""

from claudit.skills.index.indexer import (  # noqa: F401
    FunctionDef,
    FunctionBody,
    GlobalNotFoundError,
    CtagsNotFoundError,
    IndexingError,
    ensure_index,
    find_definition,
    find_references,
    get_ctags_tags,
    get_function_body,
    list_symbols,
    gtags_mtime,
    _find_project_root,
    _check_global,
    _check_gtags,
    _check_ctags,
    _ctags_function_bounds,
)
