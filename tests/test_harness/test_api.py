"""Tests for the harness skill public API."""

import pytest
from claudit.skills.harness import (
    extract_function,
    extract_functions,
    extract_file,
    list_functions_in_file,
    analyze_dependencies,
    get_function_signature,
    get_function_callees,
)


def test_extract_function_imports():
    """Test that extract_function can be imported."""
    assert callable(extract_function)


def test_extract_functions_imports():
    """Test that extract_functions can be imported."""
    assert callable(extract_functions)


def test_extract_file_imports():
    """Test that extract_file can be imported."""
    assert callable(extract_file)


def test_list_functions_imports():
    """Test that list_functions_in_file can be imported."""
    assert callable(list_functions_in_file)


def test_analyze_dependencies_imports():
    """Test that analyze_dependencies can be imported."""
    assert callable(analyze_dependencies)


def test_get_function_signature_imports():
    """Test that get_function_signature can be imported."""
    assert callable(get_function_signature)


def test_get_function_callees_imports():
    """Test that get_function_callees can be imported."""
    assert callable(get_function_callees)


def test_extract_function_signature():
    """Test extract_function has correct signature."""
    import inspect

    sig = inspect.signature(extract_function)
    params = list(sig.parameters.keys())

    assert "project_dir" in params
    assert "function_name" in params
    assert "language" in params


def test_extract_functions_signature():
    """Test extract_functions has correct signature."""
    import inspect

    sig = inspect.signature(extract_functions)
    params = list(sig.parameters.keys())

    assert "project_dir" in params
    assert "function_names" in params
    assert "language" in params


def test_extract_file_signature():
    """Test extract_file has correct signature."""
    import inspect

    sig = inspect.signature(extract_file)
    params = list(sig.parameters.keys())

    assert "project_dir" in params
    assert "filepath" in params
    assert "language" in params


def test_analyze_dependencies_signature():
    """Test analyze_dependencies has correct signature."""
    import inspect

    sig = inspect.signature(analyze_dependencies)
    params = list(sig.parameters.keys())

    assert "project_dir" in params
    assert "function_names" in params
    assert "depth" in params


def test_get_function_signature_signature():
    """Test get_function_signature has correct signature."""
    import inspect

    sig = inspect.signature(get_function_signature)
    params = list(sig.parameters.keys())

    assert "project_dir" in params
    assert "function_name" in params
    assert "language" in params


def test_get_function_callees_signature():
    """Test get_function_callees has correct signature."""
    import inspect

    sig = inspect.signature(get_function_callees)
    params = list(sig.parameters.keys())

    assert "project_dir" in params
    assert "function_name" in params


# Integration tests would go here, but they require a real project
# with gtags and ctags installed, so we'll keep them simple for now
