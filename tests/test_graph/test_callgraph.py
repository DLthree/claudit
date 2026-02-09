"""Tests for call graph extraction — uses real Pygments tokenization."""

from pathlib import Path
from unittest.mock import patch, MagicMock

from claudit.skills.index.indexer import FunctionDef, FunctionBody
from claudit.skills.graph.callgraph import (
    _extract_calls_from_source,
    _callees_of,
    build_call_graph,
    _find_enclosing_function,
    _resolve_c_function_pointers,
)


# ---------------------------------------------------------------------------
# _extract_calls_from_source — pure function, no mocking needed
# ---------------------------------------------------------------------------
class TestExtractCallsFromSource:
    def test_c_simple_calls(self):
        source = "void foo() {\n    bar(x, y);\n    baz();\n}"
        known = {"foo", "bar", "baz"}
        calls = _extract_calls_from_source(source, "c", known)
        assert "bar" in calls
        assert "baz" in calls

    def test_c_no_false_positives_on_variables(self):
        source = "void foo() {\n    int bar = 5;\n}"
        calls = _extract_calls_from_source(source, "c", {"foo", "bar"})
        assert "bar" not in calls

    def test_c_nested_calls(self):
        source = "void foo() {\n    bar(baz(x));\n}"
        calls = _extract_calls_from_source(source, "c", {"foo", "bar", "baz"})
        assert "bar" in calls
        assert "baz" in calls

    def test_ignores_unknown_symbols(self):
        # printf is not in known_symbols, so should not appear
        source = "void foo() {\n    printf(\"hello\");\n}"
        calls = _extract_calls_from_source(source, "c", {"bar"})
        assert "printf" not in calls
        assert "bar" not in calls

    def test_python_calls(self):
        source = "def foo():\n    bar(x)\n    baz()\n"
        calls = _extract_calls_from_source(source, "python", {"foo", "bar", "baz"})
        assert "bar" in calls
        assert "baz" in calls

    def test_java_calls(self):
        source = "void foo() {\n    bar(x);\n    baz();\n}"
        calls = _extract_calls_from_source(source, "java", {"foo", "bar", "baz"})
        assert "bar" in calls
        assert "baz" in calls

    def test_unknown_language_returns_empty(self):
        assert _extract_calls_from_source("foo()", "rust", {"foo"}) == []


# ---------------------------------------------------------------------------
# _callees_of — needs mocked Global but uses real tokenization
# ---------------------------------------------------------------------------
class TestCalleesOf:
    def test_extracts_calls(self):
        func_def = FunctionDef(name="foo", file="main.c", line=1)
        func_body = FunctionBody(
            file="main.c", start_line=1, end_line=3,
            source="void foo() {\n    bar();\n}",
        )
        with patch("claudit.skills.graph.callgraph.find_definition", return_value=[func_def]), \
             patch("claudit.skills.graph.callgraph.get_function_body", return_value=func_body):
            calls = _callees_of("foo", "/proj", "c", {"foo", "bar"})
        assert "bar" in calls

    def test_no_definition_returns_empty(self):
        with patch("claudit.skills.graph.callgraph.find_definition", return_value=[]):
            assert _callees_of("foo", "/proj", "c", {"foo"}) == []

    def test_no_body_returns_empty(self):
        func_def = FunctionDef(name="foo", file="main.c", line=1)
        with patch("claudit.skills.graph.callgraph.find_definition", return_value=[func_def]), \
             patch("claudit.skills.graph.callgraph.get_function_body", return_value=None):
            assert _callees_of("foo", "/proj", "c", {"foo"}) == []


# ---------------------------------------------------------------------------
# build_call_graph — integration test with mocked Global
# ---------------------------------------------------------------------------
class TestBuildCallGraph:
    def test_builds_graph(self):
        func_def = FunctionDef(name="foo", file="main.c", line=1)
        func_body = FunctionBody(
            file="main.c", start_line=1, end_line=3,
            source="void foo() {\n    bar();\n}",
        )
        with patch("claudit.skills.graph.callgraph.list_symbols", return_value=["foo", "bar"]), \
             patch("claudit.skills.graph.callgraph.find_definition", return_value=[func_def]), \
             patch("claudit.skills.graph.callgraph.get_function_body", return_value=func_body), \
             patch("claudit.skills.graph.callgraph._resolve_c_function_pointers", return_value={}):
            graph = build_call_graph("/proj", "c")
        assert "foo" in graph
        assert "bar" in graph["foo"]

    def test_overrides_merged(self):
        with patch("claudit.skills.graph.callgraph.list_symbols", return_value=["foo", "bar"]), \
             patch("claudit.skills.graph.callgraph.find_definition", return_value=[]), \
             patch("claudit.skills.graph.callgraph.get_function_body", return_value=None), \
             patch("claudit.skills.graph.callgraph._resolve_c_function_pointers", return_value={}):
            graph = build_call_graph("/proj", "c", overrides={"foo": ["bar", "baz"]})
        assert sorted(graph["foo"]) == ["bar", "baz"]

    def test_python_skips_function_pointers(self):
        with patch("claudit.skills.graph.callgraph.list_symbols", return_value=["foo"]), \
             patch("claudit.skills.graph.callgraph.find_definition", return_value=[]), \
             patch("claudit.skills.graph.callgraph.get_function_body", return_value=None), \
             patch("claudit.skills.graph.callgraph._resolve_c_function_pointers") as mock_fp:
            build_call_graph("/proj", "python")
        mock_fp.assert_not_called()


# ---------------------------------------------------------------------------
# _find_enclosing_function / _resolve_c_function_pointers
# ---------------------------------------------------------------------------
class TestFindEnclosingFunction:
    def test_finds_nearest_above(self, tmp_path):
        global_output = "init_module 5 init.c void init_module() {\nhelper 20 init.c void helper() {"
        filepath = tmp_path / "init.c"
        filepath.write_text("")
        with patch("shutil.which", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=MagicMock(stdout=global_output)):
            assert _find_enclosing_function(filepath, 10, str(tmp_path)) == "init_module"

    def test_no_global_returns_none(self, tmp_path):
        with patch("shutil.which", return_value=None):
            assert _find_enclosing_function(tmp_path / "f.c", 10, str(tmp_path)) is None

    def test_outside_project_returns_none(self, tmp_path):
        with patch("shutil.which", return_value="/usr/bin/global"):
            assert _find_enclosing_function(Path("/other/file.c"), 10, str(tmp_path)) is None


class TestResolveCFunctionPointers:
    def test_no_rg_returns_empty(self):
        with patch("shutil.which", return_value=None):
            assert _resolve_c_function_pointers("/proj", {"foo"}) == {}

    def test_parses_rg_output(self, tmp_path):
        rg_output = "init.c:10: .handler = my_func\n"
        with patch("shutil.which", return_value="/usr/bin/rg"), \
             patch("subprocess.run", return_value=MagicMock(stdout=rg_output)), \
             patch("claudit.skills.graph.callgraph._find_enclosing_function", return_value="init_module"):
            result = _resolve_c_function_pointers(str(tmp_path), {"my_func"})
        assert "init_module" in result
        assert "my_func" in result["init_module"]
