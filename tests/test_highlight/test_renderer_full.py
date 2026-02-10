"""Additional tests for highlight renderer covering edge cases.

Tests for _hex_to_rgba, _definition_span reading from files,
and highlight_path with bodies that don't contain the call.
"""

from unittest.mock import patch

from claudit.skills.index.indexer import FunctionDef, FunctionBody
from claudit.skills.highlight.renderer import (
    _hex_to_rgba,
    _definition_span,
    _find_call_site,
    _highlight_source,
    highlight_function,
    highlight_path,
)


# ---------------------------------------------------------------------------
# _hex_to_rgba — pure function
# ---------------------------------------------------------------------------
class TestHexToRgba:
    def test_standard_color(self):
        result = _hex_to_rgba("#FF6B6B", alpha=0.3)
        assert result == "rgba(255, 107, 107, 0.3)"

    def test_black(self):
        result = _hex_to_rgba("#000000", alpha=0.5)
        assert result == "rgba(0, 0, 0, 0.5)"

    def test_white(self):
        result = _hex_to_rgba("#FFFFFF", alpha=1.0)
        assert result == "rgba(255, 255, 255, 1.0)"

    def test_no_hash_prefix(self):
        result = _hex_to_rgba("4ECDC4", alpha=0.3)
        assert result == "rgba(78, 205, 196, 0.3)"

    def test_invalid_length_returns_default(self):
        result = _hex_to_rgba("#FFF", alpha=0.3)
        assert result == "rgba(0, 0, 0, 0.3)"


# ---------------------------------------------------------------------------
# _definition_span — reading from real files
# ---------------------------------------------------------------------------
class TestDefinitionSpanFromFile:
    def test_reads_from_real_file(self, tmp_path):
        """When no definition_line is passed, reads from the actual file."""
        src = "int x;\nvoid helper(int n) {\n    return;\n}\n"
        (tmp_path / "util.c").write_text(src)
        func_def = FunctionDef(name="helper", file="util.c", line=2)

        linenum, col_start, col_end = _definition_span(func_def, str(tmp_path))
        assert linenum == 2
        # "void helper" — "helper" starts at index 5, 1-based = 6
        assert col_start == 6
        assert col_end == 11  # "helper" is 6 chars, 5+6=11

    def test_missing_file_returns_defaults(self, tmp_path):
        func_def = FunctionDef(name="foo", file="missing.c", line=5)
        linenum, col_start, col_end = _definition_span(func_def, str(tmp_path))
        assert linenum == 5
        assert col_start == 1
        assert col_end == 1

    def test_line_out_of_range(self, tmp_path):
        (tmp_path / "tiny.c").write_text("int x;\n")
        func_def = FunctionDef(name="foo", file="tiny.c", line=999)
        linenum, col_start, col_end = _definition_span(func_def, str(tmp_path))
        assert linenum == 999
        assert col_start == 1
        assert col_end == 1


# ---------------------------------------------------------------------------
# _find_call_site — edge cases
# ---------------------------------------------------------------------------
class TestFindCallSiteEdgeCases:
    def test_name_appears_but_no_parens(self):
        """Name used in non-call context (e.g., as argument) is not matched."""
        body = FunctionBody(
            file="f.c", start_line=1, end_line=3,
            source="void foo() {\n    int helper = 5;\n}"
        )
        assert _find_call_site(body, "helper") is None

    def test_multiple_occurrences_picks_call(self):
        """When name appears twice, the actual call (with parens) is found."""
        body = FunctionBody(
            file="f.c", start_line=10, end_line=14,
            source="void foo() {\n    // helper is a great function\n    helper(42);\n}"
        )
        site = _find_call_site(body, "helper")
        assert site is not None
        assert site["line"] == 12  # start_line(10) + line_index(2)
        assert site["callee"] == "helper"

    def test_call_with_spaces_before_paren(self):
        """Call with whitespace between name and ( should still match."""
        body = FunctionBody(
            file="f.c", start_line=1, end_line=3,
            source="void foo() {\n    helper  (arg);\n}"
        )
        site = _find_call_site(body, "helper")
        assert site is not None
        assert site["callee"] == "helper"


# ---------------------------------------------------------------------------
# _highlight_source — edge cases
# ---------------------------------------------------------------------------
class TestHighlightSourceEdgeCases:
    def test_java_highlighting(self):
        html = _highlight_source(
            "public static void main(String[] args) {}", "java", "monokai"
        )
        assert "<span" in html

    def test_empty_source(self):
        html = _highlight_source("", "c", "monokai")
        # Empty source should produce empty or minimal HTML
        assert isinstance(html, str)


# ---------------------------------------------------------------------------
# highlight_function — body not found
# ---------------------------------------------------------------------------
class TestHighlightFunctionNoBody:
    def test_returns_none_when_body_not_found(self, tmp_path):
        """If definition exists but body can't be extracted, return None."""
        func_def = FunctionDef(name="decl_only", file="header.h", line=5)
        with patch("claudit.skills.highlight.renderer.find_definition", return_value=[func_def]), \
             patch("claudit.skills.highlight.renderer.get_function_body", return_value=None), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = highlight_function(str(tmp_path), "decl_only")
        assert result is None


# ---------------------------------------------------------------------------
# highlight_path — call site not found in body
# ---------------------------------------------------------------------------
class TestHighlightPathNoCallSite:
    def test_skips_call_site_when_not_found(self, tmp_path):
        """When the callee name isn't found in the caller's body, no call-site result is emitted."""
        path_list = ["main", "target"]

        def mock_find_def(name, proj):
            return [FunctionDef(name=name, file=f"{name}.c", line=1)]

        def mock_get_body(func_def, proj, lang):
            # main's body does NOT contain "target("
            return FunctionBody(
                file=func_def.file, start_line=1, end_line=3,
                source=f"void {func_def.name}() {{\n    x = 1;\n}}",
            )

        with patch("claudit.skills.highlight.renderer.find_definition", side_effect=mock_find_def), \
             patch("claudit.skills.highlight.renderer.get_function_body", side_effect=mock_get_body), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = highlight_path(str(tmp_path), path_list)

        # Should have 2 definition results but NO call-site result
        assert len(result["results"]) == 2
        for r in result["results"]:
            assert r["description"].startswith("definition of")

    def test_body_none_for_intermediate_hop(self, tmp_path):
        """When body extraction fails for a caller, no call-site is emitted."""
        path_list = ["main", "target"]

        def mock_find_def(name, proj):
            return [FunctionDef(name=name, file=f"{name}.c", line=1)]

        with patch("claudit.skills.highlight.renderer.find_definition", side_effect=mock_find_def), \
             patch("claudit.skills.highlight.renderer.get_function_body", return_value=None), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = highlight_path(str(tmp_path), path_list)

        assert len(result["results"]) == 2
