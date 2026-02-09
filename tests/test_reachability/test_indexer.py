"""Tests for the indexer module (ctags-based body extraction)."""

import subprocess
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from claudit.skills.reachability.indexer import (
    FunctionDef,
    FunctionBody,
    GlobalNotFoundError,
    CtagsNotFoundError,
    IndexingError,
    get_ctags_tags,
    get_function_body,
    ensure_index,
    _find_project_root,
    gtags_mtime,
    find_definition,
    find_references,
    list_symbols,
    _ctags_function_bounds,
)


# ---------------------------------------------------------------------------
# ensure_index
# ---------------------------------------------------------------------------
class TestEnsureIndex:
    def test_existing_gtags_skips_indexing(self, tmp_path):
        """If GTAGS already exists, gtags is not invoked."""
        (tmp_path / "GTAGS").write_text("fake")
        root = ensure_index(str(tmp_path))
        assert root == tmp_path.resolve()

    def test_runs_gtags_when_missing(self, tmp_path):
        """If GTAGS is missing, gtags should be invoked."""
        mock_result = MagicMock(returncode=0, stderr="")
        with patch("claudit.skills.reachability.indexer._check_gtags", return_value="/usr/bin/gtags"), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            root = ensure_index(str(tmp_path))
        assert root == tmp_path.resolve()
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["/usr/bin/gtags"]

    def test_raises_on_gtags_failure(self, tmp_path):
        """If gtags exits non-zero, IndexingError is raised."""
        mock_result = MagicMock(returncode=1, stderr="some error")
        with patch("claudit.skills.reachability.indexer._check_gtags", return_value="/usr/bin/gtags"), \
             patch("subprocess.run", return_value=mock_result):
            with pytest.raises(IndexingError, match="gtags failed"):
                ensure_index(str(tmp_path))

    def test_raises_if_not_a_directory(self, tmp_path):
        fake = tmp_path / "nope"
        with pytest.raises(FileNotFoundError, match="does not exist"):
            ensure_index(str(fake))


# ---------------------------------------------------------------------------
# _find_project_root
# ---------------------------------------------------------------------------
class TestFindProjectRoot:
    def test_valid_directory(self, tmp_path):
        assert _find_project_root(str(tmp_path)) == tmp_path.resolve()

    def test_nonexistent_directory(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            _find_project_root(str(tmp_path / "nonexistent"))


# ---------------------------------------------------------------------------
# gtags_mtime
# ---------------------------------------------------------------------------
class TestGtagsMtime:
    def test_returns_mtime_when_exists(self, tmp_path):
        gtags = tmp_path / "GTAGS"
        gtags.write_text("data")
        mtime = gtags_mtime(str(tmp_path))
        assert mtime > 0

    def test_returns_zero_when_absent(self, tmp_path):
        assert gtags_mtime(str(tmp_path)) == 0.0


# ---------------------------------------------------------------------------
# find_definition
# ---------------------------------------------------------------------------
class TestFindDefinition:
    def test_parses_global_output(self, tmp_path):
        mock_result = MagicMock(
            stdout="main.c:10: int foo(void) {\nutil.c:20: void foo(int x) {",
            returncode=0,
        )
        with patch("claudit.skills.reachability.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            defs = find_definition("foo", str(tmp_path))

        assert len(defs) == 2
        assert defs[0].name == "foo"
        assert defs[0].file == "main.c"
        assert defs[0].line == 10
        assert defs[1].file == "util.c"
        assert defs[1].line == 20

    def test_empty_output(self, tmp_path):
        mock_result = MagicMock(stdout="", returncode=0)
        with patch("claudit.skills.reachability.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            defs = find_definition("nonexistent", str(tmp_path))
        assert defs == []


# ---------------------------------------------------------------------------
# find_references
# ---------------------------------------------------------------------------
class TestFindReferences:
    def test_parses_global_output(self, tmp_path):
        mock_result = MagicMock(
            stdout="caller.c:15: foo(args);\ncaller2.c:30: foo();",
            returncode=0,
        )
        with patch("claudit.skills.reachability.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            refs = find_references("foo", str(tmp_path))

        assert len(refs) == 2
        assert refs[0].file == "caller.c"
        assert refs[0].line == 15
        assert refs[1].file == "caller2.c"
        assert refs[1].line == 30

    def test_empty_output(self, tmp_path):
        mock_result = MagicMock(stdout="", returncode=0)
        with patch("claudit.skills.reachability.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            refs = find_references("nonexistent", str(tmp_path))
        assert refs == []


# ---------------------------------------------------------------------------
# list_symbols
# ---------------------------------------------------------------------------
class TestListSymbols:
    def test_parses_output(self, tmp_path):
        mock_result = MagicMock(stdout="foo\nbar\nbaz\n", returncode=0)
        with patch("claudit.skills.reachability.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            symbols = list_symbols(str(tmp_path))
        assert symbols == ["foo", "bar", "baz"]

    def test_empty_output(self, tmp_path):
        mock_result = MagicMock(stdout="", returncode=0)
        with patch("claudit.skills.reachability.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            symbols = list_symbols(str(tmp_path))
        assert symbols == []


# ---------------------------------------------------------------------------
# get_ctags_tags (mocked)
# ---------------------------------------------------------------------------
class TestCtagsTags:
    """Verify ctags --output-format=json --fields=+ne produces usable output."""

    def test_parses_json_tags(self, tmp_path):
        src = tmp_path / "test.c"
        src.write_text("void foo() { bar(); }")
        ctags_output = (
            '{"_type": "tag", "name": "foo", "line": 1, "kind": "function", "end": 3}\n'
            '{"_type": "ptag", "name": "!_TAG"}\n'
            '{"_type": "tag", "name": "bar", "line": 2, "kind": "function", "end": 4}\n'
        )
        mock_result = MagicMock(stdout=ctags_output, returncode=0)
        with patch("claudit.skills.reachability.indexer._check_ctags", return_value="/usr/bin/ctags"), \
             patch("subprocess.run", return_value=mock_result):
            tags = get_ctags_tags(str(src))

        assert len(tags) == 2
        assert tags[0]["name"] == "foo"
        assert tags[0]["end"] == 3
        assert tags[1]["name"] == "bar"

    def test_skips_invalid_json_lines(self, tmp_path):
        src = tmp_path / "test.c"
        src.write_text("void foo() {}")
        ctags_output = (
            'not json at all\n'
            '{"_type": "tag", "name": "foo", "line": 1, "kind": "function"}\n'
            '\n'
        )
        mock_result = MagicMock(stdout=ctags_output, returncode=0)
        with patch("claudit.skills.reachability.indexer._check_ctags", return_value="/usr/bin/ctags"), \
             patch("subprocess.run", return_value=mock_result):
            tags = get_ctags_tags(str(src))

        assert len(tags) == 1
        assert tags[0]["name"] == "foo"

    def test_empty_output(self, tmp_path):
        src = tmp_path / "empty.c"
        src.write_text("")
        mock_result = MagicMock(stdout="", returncode=0)
        with patch("claudit.skills.reachability.indexer._check_ctags", return_value="/usr/bin/ctags"), \
             patch("subprocess.run", return_value=mock_result):
            tags = get_ctags_tags(str(src))
        assert tags == []


# ---------------------------------------------------------------------------
# _ctags_function_bounds (mocked)
# ---------------------------------------------------------------------------
class TestCtagsFunctionBounds:
    def test_exact_match(self, tmp_path):
        src = tmp_path / "test.c"
        src.write_text("void foo() {}")
        tags = [
            {"_type": "tag", "name": "foo", "line": 1, "kind": "function", "end": 3},
        ]
        with patch("claudit.skills.reachability.indexer.get_ctags_tags", return_value=tags):
            bounds = _ctags_function_bounds(str(src), "foo", 1)
        assert bounds == (1, 3)

    def test_fallback_by_name(self, tmp_path):
        src = tmp_path / "test.c"
        src.write_text("void foo() {}")
        tags = [
            {"_type": "tag", "name": "foo", "line": 5, "kind": "function", "end": 10},
        ]
        with patch("claudit.skills.reachability.indexer.get_ctags_tags", return_value=tags):
            # start_line=1 doesn't match line=5, but fallback matches on name
            bounds = _ctags_function_bounds(str(src), "foo", 1)
        assert bounds == (5, 10)

    def test_returns_none_when_no_match(self, tmp_path):
        src = tmp_path / "test.c"
        src.write_text("void foo() {}")
        tags = [
            {"_type": "tag", "name": "bar", "line": 1, "kind": "function", "end": 3},
        ]
        with patch("claudit.skills.reachability.indexer.get_ctags_tags", return_value=tags):
            bounds = _ctags_function_bounds(str(src), "foo", 1)
        assert bounds is None

    def test_returns_none_when_no_end(self, tmp_path):
        src = tmp_path / "test.c"
        src.write_text("void foo() {}")
        tags = [
            {"_type": "tag", "name": "foo", "line": 1, "kind": "function"},
        ]
        with patch("claudit.skills.reachability.indexer.get_ctags_tags", return_value=tags):
            bounds = _ctags_function_bounds(str(src), "foo", 1)
        assert bounds is None


# ---------------------------------------------------------------------------
# get_function_body (mocked)
# ---------------------------------------------------------------------------
class TestGetFunctionBody:
    """Test get_function_body with mocked ctags bounds."""

    def test_extracts_body(self, tmp_path):
        src = tmp_path / "main.c"
        src.write_text("void foo() {\n    bar();\n}\nvoid other() {\n    baz();\n}\n")
        func = FunctionDef(name="foo", file="main.c", line=1)
        with patch(
            "claudit.skills.reachability.indexer._ctags_function_bounds",
            return_value=(1, 3),
        ):
            body = get_function_body(func, str(tmp_path), "c")
        assert body is not None
        assert body.start_line == 1
        assert body.end_line == 3
        assert "bar();" in body.source
        assert "baz" not in body.source

    def test_missing_file_returns_none(self, tmp_path):
        func = FunctionDef(name="foo", file="nope.c", line=1)
        body = get_function_body(func, str(tmp_path), "c")
        assert body is None

    def test_no_bounds_returns_none(self, tmp_path):
        src = tmp_path / "main.c"
        src.write_text("void foo() { bar(); }")
        func = FunctionDef(name="foo", file="main.c", line=1)
        with patch(
            "claudit.skills.reachability.indexer._ctags_function_bounds",
            return_value=None,
        ):
            body = get_function_body(func, str(tmp_path), "c")
        assert body is None

    def test_clamps_to_file_length(self, tmp_path):
        src = tmp_path / "main.c"
        src.write_text("line1\nline2\n")
        func = FunctionDef(name="foo", file="main.c", line=1)
        with patch(
            "claudit.skills.reachability.indexer._ctags_function_bounds",
            return_value=(1, 100),  # end_line way beyond file
        ):
            body = get_function_body(func, str(tmp_path), "c")
        assert body is not None
        assert body.source == "line1\nline2"


# ---------------------------------------------------------------------------
# Error classes
# ---------------------------------------------------------------------------
class TestErrorClasses:
    def test_global_not_found_error(self):
        with patch("shutil.which", return_value=None):
            with pytest.raises(GlobalNotFoundError, match="GNU Global"):
                from claudit.skills.reachability.indexer import _check_global
                _check_global()

    def test_ctags_not_found_error(self):
        with patch("shutil.which", return_value=None):
            with pytest.raises(CtagsNotFoundError, match="Universal Ctags"):
                from claudit.skills.reachability.indexer import _check_ctags
                _check_ctags()

    def test_check_global_returns_path(self):
        with patch("shutil.which", return_value="/usr/bin/global"):
            from claudit.skills.reachability.indexer import _check_global
            assert _check_global() == "/usr/bin/global"

    def test_check_gtags_returns_path(self):
        with patch("shutil.which", return_value="/usr/bin/gtags"):
            from claudit.skills.reachability.indexer import _check_gtags
            assert _check_gtags() == "/usr/bin/gtags"

    def test_check_gtags_raises(self):
        with patch("shutil.which", return_value=None):
            with pytest.raises(GlobalNotFoundError):
                from claudit.skills.reachability.indexer import _check_gtags
                _check_gtags()
