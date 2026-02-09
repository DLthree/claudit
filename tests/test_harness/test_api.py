"""Tests for the harness skill public API."""

import pytest
from claudit.skills.harness import extract_functions, extract_file


def test_extract_functions_imports():
    """Test that extract_functions can be imported."""
    assert callable(extract_functions)


def test_extract_file_imports():
    """Test that extract_file can be imported."""
    assert callable(extract_file)


def test_extract_functions_signature():
    """Test extract_functions has correct signature."""
    import inspect

    sig = inspect.signature(extract_functions)
    params = list(sig.parameters.keys())

    assert "project_dir" in params
    assert "function_names" in params
    assert "language" in params
    assert "include_main" in params
    assert "stub_depth" in params
    assert "auto_index" in params


def test_extract_file_signature():
    """Test extract_file has correct signature."""
    import inspect

    sig = inspect.signature(extract_file)
    params = list(sig.parameters.keys())

    assert "project_dir" in params
    assert "filepath" in params
    assert "language" in params
    assert "include_main" in params
    assert "stub_depth" in params
    assert "auto_index" in params


# Integration tests would go here, but they require a real project
# with gtags and ctags installed, so we'll keep them simple for now
