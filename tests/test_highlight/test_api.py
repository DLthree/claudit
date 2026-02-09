"""Tests for the /highlight skill public API."""

from unittest.mock import patch

from claudit.skills.index.indexer import FunctionDef, FunctionBody
from claudit.skills.highlight import highlight_function, highlight_path


class TestHighlightFunction:
    def test_returns_highlighted_source(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        src = tmp_path / "main.c"
        src.write_text("void foo() {\n    bar();\n}\n")
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
        assert result["file"] == "main.c"
        assert "source" in result
        assert "highlighted_html" in result
        assert len(result["highlighted_html"]) > 0

    def test_returns_none_for_unknown(self, tmp_path):
        with patch("claudit.skills.highlight.renderer.find_definition", return_value=[]), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = highlight_function(str(tmp_path), "nonexistent")
        assert result is None


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
        # Each hop should have a unique color
        colors = [h["color"] for h in result["highlights"]]
        assert len(set(colors)) == 3
        # First hop should be marked as entry point
        assert "Entry point" in result["highlights"][0]["note"]
        # Last hop should be marked as target
        assert "Target" in result["highlights"][2]["note"]

    def test_handles_unknown_function(self, tmp_path):
        with patch("claudit.skills.highlight.renderer.find_definition", return_value=[]), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = highlight_path(str(tmp_path), ["unknown"])

        assert result["path_length"] == 1
        assert result["highlights"][0]["file"] == "<unknown>"
        assert "not found" in result["highlights"][0]["note"]

    def test_call_site_detected(self, tmp_path):
        func_def = FunctionDef(name="main", file="main.c", line=1)
        func_body = FunctionBody(
            file="main.c", start_line=1, end_line=3,
            source="void main() {\n    helper(arg);\n}",
        )
        with patch("claudit.skills.highlight.renderer.find_definition", return_value=[func_def]), \
             patch("claudit.skills.highlight.renderer.get_function_body", return_value=func_body), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = highlight_path(str(tmp_path), ["main", "helper"])

        first_hop = result["highlights"][0]
        assert "call_site" in first_hop
        assert first_hop["call_site"]["callee"] == "helper"
        assert "helper(arg);" in first_hop["call_site"]["snippet"]
