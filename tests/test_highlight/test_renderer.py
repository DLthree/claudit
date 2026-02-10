"""Tests for the highlight renderer — uses real Pygments highlighting."""

from unittest.mock import patch

from claudit.skills.index.indexer import FunctionDef, FunctionBody
from claudit.skills.highlight.renderer import (
    highlight_function,
    highlight_path,
    _highlight_source,
    _build_hop_note,
    _find_call_site,
    _definition_span,
    HOP_COLORS,
)


# ---------------------------------------------------------------------------
# _highlight_source — pure function, real Pygments
# ---------------------------------------------------------------------------
class TestHighlightSource:
    def test_c_produces_html(self):
        html = _highlight_source("int x = 42;", "c", "monokai")
        assert "<span" in html  # Pygments wraps tokens in spans

    def test_python_produces_html(self):
        html = _highlight_source("def foo(): pass", "python", "monokai")
        assert "<span" in html

    def test_unknown_language_returns_source(self):
        src = "some random text"
        assert _highlight_source(src, "brainfuck_nonexistent_xyz", "monokai") == src


# ---------------------------------------------------------------------------
# _build_hop_note — pure function
# ---------------------------------------------------------------------------
class TestBuildHopNote:
    def test_entry_point(self):
        note = _build_hop_note(0, "main", ["main", "helper", "target"])
        assert "Entry point" in note
        assert "helper()" in note

    def test_target(self):
        note = _build_hop_note(2, "target", ["main", "helper", "target"])
        assert "Target" in note
        assert "helper()" in note

    def test_intermediate(self):
        note = _build_hop_note(1, "helper", ["main", "helper", "target"])
        assert "Intermediate" in note
        assert "main()" in note
        assert "target()" in note

    def test_single_hop(self):
        note = _build_hop_note(0, "main", ["main"])
        assert "single-hop" in note


# ---------------------------------------------------------------------------
# _find_call_site — pure function
# ---------------------------------------------------------------------------
class TestFindCallSite:
    def test_finds_call(self):
        body = FunctionBody(file="f.c", start_line=10, end_line=15,
                            source="void foo() {\n    helper(arg);\n}")
        site = _find_call_site(body, "helper")
        assert site is not None
        assert site["callee"] == "helper"
        assert site["line"] == 11
        assert "helper(arg);" in site["snippet"]
        # Column span: "    helper" -> helper at 0-based index 4, 1-based col_start=5, col_end=10
        assert site["col_start"] == 5
        assert site["col_end"] == 10

    def test_not_found(self):
        body = FunctionBody(file="f.c", start_line=1, end_line=3,
                            source="void foo() {\n    x = 1;\n}")
        assert _find_call_site(body, "helper") is None


# ---------------------------------------------------------------------------
# _definition_span — pure function
# ---------------------------------------------------------------------------
class TestDefinitionSpan:
    def test_finds_name_on_line(self):
        func_def = FunctionDef(name="foo", file="main.c", line=1)
        line = "void foo() {"
        linenum, col_start, col_end = _definition_span(func_def, "/project", definition_line=line)
        assert linenum == 1
        assert col_start == 6   # "void " is 5 chars, 1-based => 6
        assert col_end == 8     # "foo" ends at 1-based 8

    def test_python_def(self):
        func_def = FunctionDef(name="bar", file="m.py", line=10)
        line = "def bar():"
        linenum, col_start, col_end = _definition_span(func_def, "/project", definition_line=line)
        assert linenum == 10
        assert col_start == 5
        assert col_end == 7

    def test_name_not_found_returns_whole_line(self):
        func_def = FunctionDef(name="baz", file="x.c", line=2)
        line = "  something else"
        linenum, col_start, col_end = _definition_span(func_def, "/project", definition_line=line)
        assert linenum == 2
        assert col_start == 1
        assert col_end == max(1, len(line))


# ---------------------------------------------------------------------------
# highlight_function — needs mocked Global
# ---------------------------------------------------------------------------
class TestHighlightFunction:
    def test_returns_highlighted(self, tmp_path):
        func_def = FunctionDef(name="foo", file="main.c", line=1)
        func_body = FunctionBody(
            file="main.c", start_line=1, end_line=3,
            source="void foo() {\n    bar();\n}",
        )
        with patch("claudit.skills.highlight.renderer.find_definition", return_value=[func_def]), \
             patch("claudit.skills.highlight.renderer.get_function_body", return_value=func_body), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = highlight_function(str(tmp_path), "foo")
        assert result is not None
        assert result["function"] == "foo"
        assert "<span" in result["highlighted_html"]
        assert result["source"] == func_body.source

    def test_returns_none_for_unknown(self, tmp_path):
        with patch("claudit.skills.highlight.renderer.find_definition", return_value=[]), \
             patch("claudit.lang.detect_language", return_value="c"):
            assert highlight_function(str(tmp_path), "nonexistent") is None


# ---------------------------------------------------------------------------
# highlight_path — integration test (RESULTS_FORMAT: metadata + results)
# ---------------------------------------------------------------------------
class TestHighlightPath:
    def test_returns_metadata_and_results(self, tmp_path):
        path_list = ["main", "helper", "target"]

        def mock_find_def(name, proj):
            return [FunctionDef(name=name, file=f"{name}.c", line=1)]

        def mock_get_body(func_def, proj, lang):
            idx = path_list.index(func_def.name) if func_def.name in path_list else -1
            next_name = path_list[idx + 1] if 0 <= idx < len(path_list) - 1 else "next"
            return FunctionBody(
                file=func_def.file, start_line=1, end_line=3,
                source=f"void {func_def.name}() {{\n    {next_name}();\n}}",
            )

        with patch("claudit.skills.highlight.renderer.find_definition", side_effect=mock_find_def), \
             patch("claudit.skills.highlight.renderer.get_function_body", side_effect=mock_get_body), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = highlight_path(str(tmp_path), path_list)

        assert "metadata" in result
        assert result["metadata"]["tool"] == "claudit"
        assert "timestamp" in result["metadata"]
        assert "results" in result
        # 5 results: def(main), call(main->helper), def(helper), call(helper->target), def(target)
        assert len(result["results"]) == 5
        for r in result["results"]:
            assert "ID" in r
            assert "description" in r
            assert "notes" in r
            assert "category" in r
            assert "severity" in r
            assert "filename" in r
            assert "linenum" in r
            assert "col_start" in r
            assert "col_end" in r
            assert "function" in r
        assert result["results"][0]["description"] == "definition of main"
        assert "Entry point" in result["results"][0]["notes"]
        assert result["results"][1]["description"] == "call to helper"
        assert result["results"][4]["description"] == "definition of target"
        assert "Target" in result["results"][4]["notes"]

    def test_handles_unknown_function(self, tmp_path):
        with patch("claudit.skills.highlight.renderer.find_definition", return_value=[]), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = highlight_path(str(tmp_path), ["unknown"])
        assert "metadata" in result
        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["filename"] == "<unknown>"
