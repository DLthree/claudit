"""Tests for the highlight renderer — uses real Pygments highlighting."""

from unittest.mock import patch

from claudit.skills.index.indexer import FunctionDef, FunctionBody
from claudit.skills.highlight.renderer import (
    highlight_function,
    highlight_path,
    _highlight_source,
    _build_hop_note,
    _find_call_site,
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

    def test_not_found(self):
        body = FunctionBody(file="f.c", start_line=1, end_line=3,
                            source="void foo() {\n    x = 1;\n}")
        assert _find_call_site(body, "helper") is None


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
# highlight_path — integration test
# ---------------------------------------------------------------------------
class TestHighlightPath:
    def test_highlights_all_hops(self, tmp_path):
        def mock_find_def(name, proj):
            return [FunctionDef(name=name, file=f"{name}.c", line=1)]

        def mock_get_body(func_def, proj, lang):
            return FunctionBody(
                file=func_def.file, start_line=1, end_line=3,
                source=f"void {func_def.name}() {{\n    next();\n}}",
            )

        with patch("claudit.skills.highlight.renderer.find_definition", side_effect=mock_find_def), \
             patch("claudit.skills.highlight.renderer.get_function_body", side_effect=mock_get_body), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = highlight_path(str(tmp_path), ["main", "helper", "target"])

        assert result["path_length"] == 3
        assert len(result["highlights"]) == 3
        # Each hop gets a distinct color
        colors = [h["color"] for h in result["highlights"]]
        assert len(set(colors)) == 3
        # First = entry, last = target
        assert "Entry point" in result["highlights"][0]["note"]
        assert "Target" in result["highlights"][2]["note"]

    def test_handles_unknown_function(self, tmp_path):
        with patch("claudit.skills.highlight.renderer.find_definition", return_value=[]), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = highlight_path(str(tmp_path), ["unknown"])
        assert result["highlights"][0]["file"] == "<unknown>"
