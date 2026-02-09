"""Shared exception classes for claudit skills."""

from __future__ import annotations


class GlobalNotFoundError(Exception):
    """Raised when GNU Global is not installed."""

    def __init__(self) -> None:
        super().__init__(
            "GNU Global (gtags/global) is not installed.\n"
            "Install it with:\n"
            "  Ubuntu/Debian: sudo apt-get install global\n"
            "  macOS:         brew install global\n"
            "  Fedora:        sudo dnf install global"
        )


class CtagsNotFoundError(Exception):
    """Raised when Universal Ctags is not installed."""

    def __init__(self) -> None:
        super().__init__(
            "Universal Ctags is not installed.\n"
            "Install it with:\n"
            "  Ubuntu/Debian: sudo apt-get install universal-ctags\n"
            "  macOS:         brew install universal-ctags\n"
            "  Fedora:        sudo dnf install ctags"
        )


class IndexingError(Exception):
    """Raised when gtags indexing fails."""


class IndexNotFoundError(Exception):
    """Raised when GTAGS index is missing and auto-indexing is disabled."""


class GraphNotFoundError(Exception):
    """Raised when call graph is missing and auto-building is disabled."""


class FunctionNotFoundError(Exception):
    """Raised when a function symbol cannot be found in the index."""
