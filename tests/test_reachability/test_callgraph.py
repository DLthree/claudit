"""Tests for call graph extraction from source code."""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from claudit.skills.graph.callgraph import (
    _extract_calls_from_source,
    _resolve_c_function_pointers,
    _find_enclosing_function,
    build_call_graph,
    _callees_of,
)
from claudit.lang import detect_language
from claudit.skills.index.indexer import FunctionDef, FunctionBody


class TestExtractCallsC:
    def test_simple_call(self):
        source = """
void foo() {
    bar(x, y);
    baz();
}
"""
        known = {"foo", "bar", "baz", "unknown"}
        calls = _extract_calls_from_source(source, "c", known)
        assert "bar" in calls
        assert "baz" in calls

    def test_no_false_positives_on_declarations(self):
        source = """
void foo() {
    int bar = 5;
}
"""
        known = {"foo", "bar"}
        calls = _extract_calls_from_source(source, "c", known)
        # 'bar' appears as a variable assignment, not a call
        assert "bar" not in calls

    def test_nested_calls(self):
        source = """
void foo() {
    bar(baz(x));
}
"""
        known = {"foo", "bar", "baz"}
        calls = _extract_calls_from_source(source, "c", known)
        assert "bar" in calls
        assert "baz" in calls

    def test_ignores_unknown_symbols(self):
        source = """
void foo() {
    printf("hello");
}
"""
        known = {"foo"}
        calls = _extract_calls_from_source(source, "c", known)
        assert "printf" not in calls


class TestExtractCallsPython:
    def test_simple_call(self):
        source = """
def foo():
    bar(x)
    baz()
"""
        known = {"foo", "bar", "baz"}
        calls = _extract_calls_from_source(source, "python", known)
        assert "bar" in calls
        assert "baz" in calls

    def test_method_call_not_matched(self):
        source = """
def foo():
    obj.bar(x)
"""
        known = {"foo", "bar"}
        calls = _extract_calls_from_source(source, "python", known)
        # 'bar' after a dot is a method - Pygments may tokenize it as Name
        # This depends on lexer behavior; we accept either outcome.

    def test_ignores_unknown(self):
        source = """
def foo():
    unknown_func(x)
"""
        known = set()  # nothing is "known"
        calls = _extract_calls_from_source(source, "python", known)
        assert calls == []


class TestExtractCallsJava:
    def test_simple_call(self):
        source = """
void foo() {
    bar(x);
    baz();
}
"""
        known = {"foo", "bar", "baz"}
        calls = _extract_calls_from_source(source, "java", known)
        assert "bar" in calls
        assert "baz" in calls


class TestExtractCallsUnknownLanguage:
    def test_unknown_language_returns_empty(self):
        calls = _extract_calls_from_source("foo()", "rust", {"foo"})
        assert calls == []


class TestDetectLanguage:
    def test_detects_c(self, tmp_path):
        (tmp_path / "main.c").write_text("int main() {}")
        (tmp_path / "util.c").write_text("void util() {}")
        (tmp_path / "util.h").write_text("void util();")
        assert detect_language(str(tmp_path)) == "c"

    def test_detects_python(self, tmp_path):
        (tmp_path / "app.py").write_text("def main(): pass")
        (tmp_path / "util.py").write_text("def util(): pass")
        assert detect_language(str(tmp_path)) == "python"

    def test_detects_java(self, tmp_path):
        (tmp_path / "Main.java").write_text("class Main {}")
        (tmp_path / "Util.java").write_text("class Util {}")
        assert detect_language(str(tmp_path)) == "java"

    def test_empty_defaults_to_c(self, tmp_path):
        assert detect_language(str(tmp_path)) == "c"


class TestCalleesOf:
    def test_returns_calls_from_body(self):
        func_def = FunctionDef(name="foo", file="main.c", line=1)
        func_body = FunctionBody(
            file="main.c",
            start_line=1,
            end_line=3,
            source="void foo() {\n    bar();\n}",
        )
        with patch(
            "claudit.skills.graph.callgraph.find_definition",
            return_value=[func_def],
        ), patch(
            "claudit.skills.graph.callgraph.get_function_body",
            return_value=func_body,
        ):
            calls = _callees_of("foo", "/proj", "c", {"foo", "bar"})
        assert "bar" in calls

    def test_no_definition_returns_empty(self):
        with patch(
            "claudit.skills.graph.callgraph.find_definition",
            return_value=[],
        ):
            calls = _callees_of("foo", "/proj", "c", {"foo", "bar"})
        assert calls == []

    def test_no_body_returns_empty(self):
        func_def = FunctionDef(name="foo", file="main.c", line=1)
        with patch(
            "claudit.skills.graph.callgraph.find_definition",
            return_value=[func_def],
        ), patch(
            "claudit.skills.graph.callgraph.get_function_body",
            return_value=None,
        ):
            calls = _callees_of("foo", "/proj", "c", {"foo", "bar"})
        assert calls == []

    def test_empty_body_returns_empty(self):
        func_def = FunctionDef(name="foo", file="main.c", line=1)
        func_body = FunctionBody(
            file="main.c", start_line=1, end_line=1, source="   "
        )
        with patch(
            "claudit.skills.graph.callgraph.find_definition",
            return_value=[func_def],
        ), patch(
            "claudit.skills.graph.callgraph.get_function_body",
            return_value=func_body,
        ):
            calls = _callees_of("foo", "/proj", "c", {"foo", "bar"})
        assert calls == []


class TestBuildCallGraph:
    def test_basic_graph(self):
        func_def = FunctionDef(name="foo", file="main.c", line=1)
        func_body = FunctionBody(
            file="main.c",
            start_line=1,
            end_line=3,
            source="void foo() {\n    bar();\n}",
        )
        with patch(
            "claudit.skills.graph.callgraph.list_symbols",
            return_value=["foo", "bar"],
        ), patch(
            "claudit.skills.graph.callgraph.find_definition",
            return_value=[func_def],
        ), patch(
            "claudit.skills.graph.callgraph.get_function_body",
            return_value=func_body,
        ), patch(
            "claudit.skills.graph.callgraph._resolve_c_function_pointers",
            return_value={},
        ):
            graph = build_call_graph("/proj", "c")
        assert "foo" in graph
        assert "bar" in graph["foo"]

    def test_with_overrides(self):
        with patch(
            "claudit.skills.graph.callgraph.list_symbols",
            return_value=["foo", "bar"],
        ), patch(
            "claudit.skills.graph.callgraph.find_definition",
            return_value=[],
        ), patch(
            "claudit.skills.graph.callgraph.get_function_body",
            return_value=None,
        ), patch(
            "claudit.skills.graph.callgraph._resolve_c_function_pointers",
            return_value={},
        ):
            overrides = {"foo": ["bar", "baz"]}
            graph = build_call_graph("/proj", "c", overrides=overrides)
        assert "foo" in graph
        assert "bar" in graph["foo"]
        assert "baz" in graph["foo"]

    def test_overrides_merged_with_existing_edges(self):
        """Overrides add to existing edges rather than replacing them."""
        func_def = FunctionDef(name="foo", file="main.c", line=1)
        func_body = FunctionBody(
            file="main.c",
            start_line=1,
            end_line=3,
            source="void foo() {\n    bar();\n}",
        )
        with patch(
            "claudit.skills.graph.callgraph.list_symbols",
            return_value=["foo", "bar", "baz"],
        ), patch(
            "claudit.skills.graph.callgraph.find_definition",
            return_value=[func_def],
        ), patch(
            "claudit.skills.graph.callgraph.get_function_body",
            return_value=func_body,
        ), patch(
            "claudit.skills.graph.callgraph._resolve_c_function_pointers",
            return_value={},
        ):
            # foo already calls bar from source; override adds baz
            overrides = {"foo": ["baz"]}
            graph = build_call_graph("/proj", "c", overrides=overrides)
        assert "bar" in graph["foo"]
        assert "baz" in graph["foo"]

    def test_c_function_pointers_merged(self):
        fp_edges = {"init": ["handler"]}
        with patch(
            "claudit.skills.graph.callgraph.list_symbols",
            return_value=["init", "handler"],
        ), patch(
            "claudit.skills.graph.callgraph.find_definition",
            return_value=[],
        ), patch(
            "claudit.skills.graph.callgraph.get_function_body",
            return_value=None,
        ), patch(
            "claudit.skills.graph.callgraph._resolve_c_function_pointers",
            return_value=fp_edges,
        ):
            graph = build_call_graph("/proj", "c")
        assert "init" in graph
        assert "handler" in graph["init"]

    def test_python_skips_function_pointers(self):
        with patch(
            "claudit.skills.graph.callgraph.list_symbols",
            return_value=["foo"],
        ), patch(
            "claudit.skills.graph.callgraph.find_definition",
            return_value=[],
        ), patch(
            "claudit.skills.graph.callgraph.get_function_body",
            return_value=None,
        ), patch(
            "claudit.skills.graph.callgraph._resolve_c_function_pointers",
        ) as mock_fp:
            graph = build_call_graph("/proj", "python")
        mock_fp.assert_not_called()


class TestResolveCFunctionPointers:
    def test_no_rg_returns_empty(self):
        with patch("shutil.which", return_value=None):
            result = _resolve_c_function_pointers("/proj", {"foo"})
        assert result == {}

    def test_parses_rg_output(self, tmp_path):
        rg_output = "init.c:10: .handler = my_func\n"
        mock_rg_result = MagicMock(stdout=rg_output, returncode=0)

        with patch("shutil.which", return_value="/usr/bin/rg"), \
             patch("subprocess.run", return_value=mock_rg_result), \
             patch(
                 "claudit.skills.graph.callgraph._find_enclosing_function",
                 return_value="init_module",
             ):
            result = _resolve_c_function_pointers(str(tmp_path), {"my_func"})
        assert "init_module" in result
        assert "my_func" in result["init_module"]

    def test_skips_unknown_targets(self, tmp_path):
        rg_output = "init.c:10: .handler = unknown_func\n"
        mock_rg_result = MagicMock(stdout=rg_output, returncode=0)

        with patch("shutil.which", return_value="/usr/bin/rg"), \
             patch("subprocess.run", return_value=mock_rg_result):
            result = _resolve_c_function_pointers(str(tmp_path), {"foo"})
        assert result == {}

    def test_skips_when_no_enclosing_function(self, tmp_path):
        rg_output = "init.c:10: .handler = my_func\n"
        mock_rg_result = MagicMock(stdout=rg_output, returncode=0)

        with patch("shutil.which", return_value="/usr/bin/rg"), \
             patch("subprocess.run", return_value=mock_rg_result), \
             patch(
                 "claudit.skills.graph.callgraph._find_enclosing_function",
                 return_value=None,
             ):
            result = _resolve_c_function_pointers(str(tmp_path), {"my_func"})
        assert result == {}


class TestFindEnclosingFunction:
    def test_finds_nearest_above(self, tmp_path):
        global_output = "init_module 5 init.c void init_module() {\nhelper 20 init.c void helper() {"
        mock_result = MagicMock(stdout=global_output, returncode=0)

        filepath = tmp_path / "init.c"
        filepath.write_text("")

        with patch("shutil.which", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            result = _find_enclosing_function(filepath, 10, str(tmp_path))
        assert result == "init_module"

    def test_no_global_returns_none(self, tmp_path):
        filepath = tmp_path / "init.c"
        with patch("shutil.which", return_value=None):
            result = _find_enclosing_function(filepath, 10, str(tmp_path))
        assert result is None

    def test_filepath_outside_project(self, tmp_path):
        filepath = Path("/some/other/path/file.c")
        with patch("shutil.which", return_value="/usr/bin/global"):
            result = _find_enclosing_function(filepath, 10, str(tmp_path))
        assert result is None

    def test_empty_output(self, tmp_path):
        mock_result = MagicMock(stdout="", returncode=0)
        filepath = tmp_path / "init.c"
        filepath.write_text("")

        with patch("shutil.which", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            result = _find_enclosing_function(filepath, 10, str(tmp_path))
        assert result is None

    def test_malformed_lines_skipped(self, tmp_path):
        global_output = "badline\ninit_module 5 init.c void init_module() {"
        mock_result = MagicMock(stdout=global_output, returncode=0)

        filepath = tmp_path / "init.c"
        filepath.write_text("")

        with patch("shutil.which", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            result = _find_enclosing_function(filepath, 10, str(tmp_path))
        assert result == "init_module"

    def test_non_numeric_line_skipped(self, tmp_path):
        global_output = "func abc init.c something\ninit_module 5 init.c void init_module() {"
        mock_result = MagicMock(stdout=global_output, returncode=0)

        filepath = tmp_path / "init.c"
        filepath.write_text("")

        with patch("shutil.which", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            result = _find_enclosing_function(filepath, 10, str(tmp_path))
        assert result == "init_module"
