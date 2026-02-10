"""Tests for function extraction from source files.

These tests mock only at the subprocess boundary (ctags, global) since
extract_target_functions and friends delegate to index.get_body and
signature_extractor which themselves call subprocess.
"""

from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

from claudit.skills.harness.extractor import (
    ExtractedFunction,
    extract_target_functions,
    extract_functions_from_file,
    list_functions_in_file,
)


# ---------------------------------------------------------------------------
# Helpers for building realistic mocks
# ---------------------------------------------------------------------------
def _make_get_body_return(name, file, source, start=1, end=5, language="c"):
    """Return dict matching index.get_body output."""
    return {
        "function": name,
        "file": file,
        "start_line": start,
        "end_line": end,
        "source": source,
        "language": language,
    }


def _make_ctags_tag(name, line, kind="function", end=None, signature="()"):
    """Return a dict matching ctags JSON output."""
    tag = {
        "_type": "tag",
        "name": name,
        "path": "test.c",
        "line": line,
        "kind": kind,
        "signature": signature,
    }
    if end is not None:
        tag["end"] = end
    return tag


# ---------------------------------------------------------------------------
# extract_target_functions
# ---------------------------------------------------------------------------
class TestExtractTargetFunctions:
    def test_extracts_single_c_function(self):
        """Extract a single C function with realistic source."""
        body = _make_get_body_return(
            "helper", "util.c",
            "void helper(int x) {\n    /* do something */\n}",
            start=3, end=5,
        )
        sig_result = MagicMock()
        sig_result.full_signature = "void helper(int x)"

        with patch("claudit.skills.harness.extractor.get_body", return_value=body), \
             patch("claudit.skills.harness.extractor.extract_signature", return_value=sig_result):
            result = extract_target_functions("/project", ["helper"], "c")

        assert len(result) == 1
        func = result[0]
        assert isinstance(func, ExtractedFunction)
        assert func.name == "helper"
        assert func.file == "util.c"
        assert func.start_line == 3
        assert func.end_line == 5
        assert "void helper" in func.source
        assert func.signature == "void helper(int x)"
        assert func.language == "c"

    def test_extracts_multiple_functions(self):
        """Extract two functions in one call."""
        bodies = {
            "main": _make_get_body_return(
                "main", "main.c",
                "int main(int argc, char **argv) {\n    return 0;\n}",
                start=7, end=9,
            ),
            "helper": _make_get_body_return(
                "helper", "util.c",
                "void helper(int x) {\n    /* work */\n}",
                start=3, end=5,
            ),
        }

        def mock_get_body(project_dir, func_name, language=None, auto_index=True):
            return bodies[func_name]

        sig = MagicMock()
        sig.full_signature = "signature"

        with patch("claudit.skills.harness.extractor.get_body", side_effect=mock_get_body), \
             patch("claudit.skills.harness.extractor.extract_signature", return_value=sig):
            result = extract_target_functions("/project", ["main", "helper"], "c")

        assert len(result) == 2
        assert result[0].name == "main"
        assert result[1].name == "helper"

    def test_raises_for_missing_function(self):
        """ValueError raised when function not found in index."""
        with patch("claudit.skills.harness.extractor.get_body", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                extract_target_functions("/project", ["nonexistent"], "c")

    def test_fallback_signature_when_ctags_fails(self):
        """When extract_signature returns None, a fallback is used."""
        body = _make_get_body_return(
            "foo", "main.c", "void foo() {}", start=1, end=1,
        )
        with patch("claudit.skills.harness.extractor.get_body", return_value=body), \
             patch("claudit.skills.harness.extractor.extract_signature", return_value=None):
            result = extract_target_functions("/project", ["foo"], "c")

        assert result[0].signature == "foo(...)"


# ---------------------------------------------------------------------------
# extract_functions_from_file
# ---------------------------------------------------------------------------
class TestExtractFunctionsFromFile:
    def test_extracts_all_functions_from_file(self, tmp_path):
        """Extract all functions from a C source file."""
        src = "void foo() {}\nint bar(int x) { return x; }\n"
        (tmp_path / "test.c").write_text(src)

        tags = [
            _make_ctags_tag("foo", 1, "function", end=1),
            _make_ctags_tag("bar", 2, "function", end=2),
        ]

        body_foo = _make_get_body_return("foo", "test.c", "void foo() {}", 1, 1)
        body_bar = _make_get_body_return("bar", "test.c", "int bar(int x) { return x; }", 2, 2)

        def mock_get_body(project_dir, func_name, language=None, auto_index=True):
            return {"foo": body_foo, "bar": body_bar}[func_name]

        sig = MagicMock()
        sig.full_signature = "sig"

        with patch("claudit.skills.harness.extractor.get_ctags_tags", return_value=tags), \
             patch("claudit.skills.harness.extractor.get_body", side_effect=mock_get_body), \
             patch("claudit.skills.harness.extractor.extract_signature", return_value=sig):
            result = extract_functions_from_file(str(tmp_path), "test.c", "c")

        assert len(result) == 2
        names = [f.name for f in result]
        assert "foo" in names
        assert "bar" in names

    def test_file_not_found(self, tmp_path):
        """FileNotFoundError raised for missing file."""
        with pytest.raises(FileNotFoundError, match="not found"):
            extract_functions_from_file(str(tmp_path), "nonexistent.c", "c")

    def test_file_with_no_functions(self, tmp_path):
        """File with only macros/typedefs returns empty list."""
        (tmp_path / "types.h").write_text("#define MAX 100\ntypedef int MyInt;\n")
        tags = [
            {"_type": "tag", "name": "MAX", "line": 1, "kind": "macro"},
            {"_type": "tag", "name": "MyInt", "line": 2, "kind": "typedef"},
        ]
        with patch("claudit.skills.harness.extractor.get_ctags_tags", return_value=tags):
            result = extract_functions_from_file(str(tmp_path), "types.h", "c")
        assert result == []

    def test_filters_only_function_kinds(self, tmp_path):
        """Only function/method/def kinds should be extracted."""
        (tmp_path / "mixed.c").write_text("int x;\nvoid foo() {}\n")
        tags = [
            {"_type": "tag", "name": "x", "line": 1, "kind": "variable"},
            _make_ctags_tag("foo", 2, "function", end=2),
        ]
        body = _make_get_body_return("foo", "mixed.c", "void foo() {}", 2, 2)
        sig = MagicMock()
        sig.full_signature = "void foo()"

        with patch("claudit.skills.harness.extractor.get_ctags_tags", return_value=tags), \
             patch("claudit.skills.harness.extractor.get_body", return_value=body), \
             patch("claudit.skills.harness.extractor.extract_signature", return_value=sig):
            result = extract_functions_from_file(str(tmp_path), "mixed.c", "c")

        assert len(result) == 1
        assert result[0].name == "foo"


# ---------------------------------------------------------------------------
# list_functions_in_file
# ---------------------------------------------------------------------------
class TestListFunctionsInFile:
    def test_lists_functions(self, tmp_path):
        """List functions by name, line, and kind."""
        (tmp_path / "app.py").write_text("def main():\n    pass\ndef helper():\n    pass\n")
        tags = [
            {"_type": "tag", "name": "main", "line": 1, "kind": "def"},
            {"_type": "tag", "name": "helper", "line": 3, "kind": "def"},
        ]
        with patch("claudit.skills.harness.extractor.get_ctags_tags", return_value=tags):
            result = list_functions_in_file(str(tmp_path), "app.py")

        assert len(result) == 2
        assert result[0] == {"name": "main", "line": 1, "kind": "def"}
        assert result[1] == {"name": "helper", "line": 3, "kind": "def"}

    def test_file_not_found(self, tmp_path):
        """FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            list_functions_in_file(str(tmp_path), "missing.py")

    def test_skips_non_function_tags(self, tmp_path):
        """Variables and macros should not appear in function list."""
        (tmp_path / "test.c").write_text("int x;\nvoid foo() {}\n")
        tags = [
            {"_type": "tag", "name": "x", "line": 1, "kind": "variable"},
            {"_type": "tag", "name": "foo", "line": 2, "kind": "function"},
        ]
        with patch("claudit.skills.harness.extractor.get_ctags_tags", return_value=tags):
            result = list_functions_in_file(str(tmp_path), "test.c")

        assert len(result) == 1
        assert result[0]["name"] == "foo"

    def test_includes_methods(self, tmp_path):
        """Method kind should be included."""
        (tmp_path / "Foo.java").write_text("class Foo { void bar() {} }")
        tags = [
            {"_type": "tag", "name": "bar", "line": 1, "kind": "method"},
        ]
        with patch("claudit.skills.harness.extractor.get_ctags_tags", return_value=tags):
            result = list_functions_in_file(str(tmp_path), "Foo.java")

        assert len(result) == 1
        assert result[0]["kind"] == "method"
