"""Integration tests for harness skill public API functions.

These tests exercise the actual orchestration logic in harness/__init__.py
by mocking only the subprocess-level operations (index, ctags, graph cache).
"""

from unittest.mock import patch, MagicMock

import pytest

from claudit.skills.harness import (
    extract_function,
    extract_functions,
    extract_file,
    analyze_dependencies,
    get_function_signature,
    get_function_callees,
    ExtractedFunction,
    DependencySet,
    FunctionSignature,
)


# ---------------------------------------------------------------------------
# extract_function
# ---------------------------------------------------------------------------
class TestExtractFunction:
    def test_extracts_with_auto_detected_language(self, c_project):
        """extract_function auto-detects language and returns result."""
        body = {
            "function": "helper",
            "file": "util.c",
            "start_line": 3,
            "end_line": 5,
            "source": "void helper(int x) {\n    /* do something */\n}",
            "language": "c",
        }
        sig = MagicMock()
        sig.full_signature = "void helper(int x)"

        with patch("claudit.skills.harness.extractor.get_body", return_value=body), \
             patch("claudit.skills.harness.extractor.extract_signature", return_value=sig):
            result = extract_function(str(c_project), "helper")

        assert result is not None
        assert isinstance(result, ExtractedFunction)
        assert result.name == "helper"
        assert result.language == "c"

    def test_raises_when_not_found(self, c_project):
        """extract_function raises ValueError for unknown function."""
        with patch("claudit.skills.harness.extractor.get_body", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                extract_function(str(c_project), "nonexistent")

    def test_explicit_language(self, python_project):
        """extract_function respects explicit language parameter."""
        body = {
            "function": "main",
            "file": "app.py",
            "start_line": 1,
            "end_line": 3,
            "source": "def main():\n    result = compute(42)\n    return result",
            "language": "python",
        }
        sig = MagicMock()
        sig.full_signature = "def main()"

        with patch("claudit.skills.harness.extractor.get_body", return_value=body), \
             patch("claudit.skills.harness.extractor.extract_signature", return_value=sig):
            result = extract_function(str(python_project), "main", language="python")

        assert result is not None
        assert result.language == "python"


# ---------------------------------------------------------------------------
# extract_functions
# ---------------------------------------------------------------------------
class TestExtractFunctions:
    def test_extracts_multiple(self, c_project):
        """extract_functions returns list of extracted functions."""
        bodies = {
            "process": {
                "function": "process",
                "file": "main.c",
                "start_line": 3,
                "end_line": 5,
                "source": "void process(int x) {\n    helper(x);\n}",
                "language": "c",
            },
            "helper": {
                "function": "helper",
                "file": "util.c",
                "start_line": 3,
                "end_line": 5,
                "source": "void helper(int x) {\n    /* do something */\n}",
                "language": "c",
            },
        }

        def mock_get_body(project_dir, func_name, language=None, auto_index=True):
            return bodies[func_name]

        sig = MagicMock()
        sig.full_signature = "sig"

        with patch("claudit.skills.harness.extractor.get_body", side_effect=mock_get_body), \
             patch("claudit.skills.harness.extractor.extract_signature", return_value=sig):
            result = extract_functions(str(c_project), ["process", "helper"])

        assert len(result) == 2
        assert result[0].name == "process"
        assert result[1].name == "helper"

    def test_raises_for_missing(self, c_project):
        """extract_functions raises ValueError if any function not found."""
        with patch("claudit.skills.harness.extractor.get_body", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                extract_functions(str(c_project), ["nonexistent"])


# ---------------------------------------------------------------------------
# extract_file
# ---------------------------------------------------------------------------
class TestExtractFile:
    def test_extracts_file(self, c_project):
        """extract_file extracts all functions from a source file."""
        tags = [
            {"_type": "tag", "name": "process", "line": 3, "kind": "function"},
            {"_type": "tag", "name": "main", "line": 7, "kind": "function"},
        ]
        bodies = {
            "process": {
                "function": "process",
                "file": "main.c",
                "start_line": 3,
                "end_line": 5,
                "source": "void process(int x) {\n    helper(x);\n}",
                "language": "c",
            },
            "main": {
                "function": "main",
                "file": "main.c",
                "start_line": 7,
                "end_line": 10,
                "source": "int main(int argc, char **argv) {\n    process(argc);\n    return 0;\n}",
                "language": "c",
            },
        }

        def mock_get_body(project_dir, func_name, language=None, auto_index=True):
            return bodies[func_name]

        sig = MagicMock()
        sig.full_signature = "sig"

        with patch("claudit.skills.harness.extractor.get_ctags_tags", return_value=tags), \
             patch("claudit.skills.harness.extractor.get_body", side_effect=mock_get_body), \
             patch("claudit.skills.harness.extractor.extract_signature", return_value=sig):
            result = extract_file(str(c_project), "main.c")

        assert len(result) == 2

    def test_missing_file_raises(self, c_project):
        with pytest.raises(FileNotFoundError):
            extract_file(str(c_project), "nonexistent.c")


# ---------------------------------------------------------------------------
# analyze_dependencies
# ---------------------------------------------------------------------------
class TestAnalyzeDependencies:
    def test_analyzes_with_cached_graph(self, c_project):
        """analyze_dependencies uses cached graph when available."""
        graph = {
            "process": ["helper", "printf"],
            "helper": [],
        }

        with patch("claudit.skills.index.indexer.ensure_index"), \
             patch("claudit.skills.graph.cache.load_call_graph", return_value=graph):
            result = analyze_dependencies(str(c_project), ["process"])

        assert isinstance(result, DependencySet)
        assert "helper" in result.stub_functions
        assert "printf" in result.excluded_stdlib

    def test_builds_graph_when_not_cached(self, c_project):
        """When no cached graph, analyze_dependencies builds one."""
        graph = {"process": ["helper"], "helper": []}

        with patch("claudit.skills.index.indexer.ensure_index"), \
             patch("claudit.skills.graph.cache.load_call_graph", side_effect=[None, graph]), \
             patch("claudit.skills.graph.build") as mock_build:
            result = analyze_dependencies(str(c_project), ["process"])

        mock_build.assert_called_once()
        assert "helper" in result.stub_functions


# ---------------------------------------------------------------------------
# get_function_signature
# ---------------------------------------------------------------------------
class TestGetFunctionSignature:
    def test_returns_signature(self, c_project):
        """get_function_signature finds and parses a function signature."""
        lookup_result = {
            "definitions": [{"name": "helper", "file": "util.c", "line": 3}],
        }
        sig = FunctionSignature(
            name="helper",
            return_type="void",
            parameters=[],
            full_signature="void helper(int x)",
        )

        with patch("claudit.skills.index.lookup", return_value=lookup_result), \
             patch("claudit.skills.harness.extract_signature", return_value=sig):
            result = get_function_signature(str(c_project), "helper")

        assert result is not None
        assert result.name == "helper"
        assert result.full_signature == "void helper(int x)"

    def test_returns_none_for_unknown(self, c_project):
        """Returns None when function not found in index."""
        with patch("claudit.skills.index.lookup", return_value={"definitions": []}):
            result = get_function_signature(str(c_project), "unknown")
        assert result is None


# ---------------------------------------------------------------------------
# get_function_callees
# ---------------------------------------------------------------------------
class TestGetFunctionCallees:
    def test_returns_callees(self, tmp_path):
        """get_function_callees returns callees from cached graph."""
        graph = {"process": ["helper", "init"], "helper": ["util"]}
        with patch("claudit.skills.graph.cache.load_call_graph", return_value=graph):
            result = get_function_callees(str(tmp_path), "process")
        assert result == ["helper", "init"]

    def test_returns_empty_for_unknown(self, tmp_path):
        """Unknown function returns empty list."""
        graph = {"process": ["helper"]}
        with patch("claudit.skills.graph.cache.load_call_graph", return_value=graph):
            result = get_function_callees(str(tmp_path), "unknown")
        assert result == []

    def test_returns_empty_when_no_graph(self, tmp_path):
        """When no cached graph exists, returns empty list."""
        with patch("claudit.skills.graph.cache.load_call_graph", return_value=None):
            result = get_function_callees(str(tmp_path), "process")
        assert result == []
