"""Tests for the index skill's low-level indexer functions.

Tests that hit subprocess (global, gtags, ctags) mock subprocess.run.
Everything else is tested against real files.
"""

from unittest.mock import patch, MagicMock

import pytest

from claudit.errors import GlobalNotFoundError, CtagsNotFoundError, IndexingError
from claudit.skills.index.indexer import (
    FunctionDef,
    FunctionBody,
    ensure_index,
    find_definition,
    find_references,
    get_ctags_tags,
    get_function_body,
    list_symbols,
    gtags_mtime,
    _find_project_root,
    _ctags_function_bounds,
)


class TestEnsureIndex:
    def test_existing_gtags_skips_indexing(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        root = ensure_index(str(tmp_path))
        assert root == tmp_path.resolve()

    def test_runs_gtags_when_missing(self, tmp_path):
        mock_result = MagicMock(returncode=0, stderr="")
        with patch("claudit.skills.index.indexer._check_gtags", return_value="/usr/bin/gtags"), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            root = ensure_index(str(tmp_path))
        assert root == tmp_path.resolve()
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["/usr/bin/gtags"]

    def test_raises_on_gtags_failure(self, tmp_path):
        mock_result = MagicMock(returncode=1, stderr="some error")
        with patch("claudit.skills.index.indexer._check_gtags", return_value="/usr/bin/gtags"), \
             patch("subprocess.run", return_value=mock_result):
            with pytest.raises(IndexingError, match="gtags failed"):
                ensure_index(str(tmp_path))

    def test_raises_if_not_a_directory(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="does not exist"):
            ensure_index(str(tmp_path / "nope"))


class TestFindProjectRoot:
    def test_valid_directory(self, tmp_path):
        assert _find_project_root(str(tmp_path)) == tmp_path.resolve()

    def test_nonexistent_directory(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            _find_project_root(str(tmp_path / "nonexistent"))


class TestGtagsMtime:
    def test_returns_mtime_when_exists(self, tmp_path):
        (tmp_path / "GTAGS").write_text("data")
        assert gtags_mtime(str(tmp_path)) > 0

    def test_returns_zero_when_absent(self, tmp_path):
        assert gtags_mtime(str(tmp_path)) == 0.0


class TestFindDefinition:
    def test_parses_global_output(self, tmp_path):
        mock_result = MagicMock(
            stdout="main.c:10: int foo(void) {\nutil.c:20: void foo(int x) {",
            returncode=0,
        )
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            defs = find_definition("foo", str(tmp_path))
        assert len(defs) == 2
        assert defs[0] == FunctionDef(name="foo", file="main.c", line=10)
        assert defs[1] == FunctionDef(name="foo", file="util.c", line=20)

    def test_empty_output(self, tmp_path):
        mock_result = MagicMock(stdout="", returncode=0)
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            assert find_definition("nonexistent", str(tmp_path)) == []


class TestFindReferences:
    def test_parses_global_output(self, tmp_path):
        mock_result = MagicMock(
            stdout="caller.c:15: foo(args);\ncaller2.c:30: foo();",
            returncode=0,
        )
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            refs = find_references("foo", str(tmp_path))
        assert len(refs) == 2
        assert refs[0].file == "caller.c"
        assert refs[1].line == 30


class TestListSymbols:
    def test_parses_output(self, tmp_path):
        mock_result = MagicMock(stdout="foo\nbar\nbaz\n", returncode=0)
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            assert list_symbols(str(tmp_path)) == ["foo", "bar", "baz"]


class TestCtagsTags:
    def test_parses_json_tags(self, tmp_path):
        src = tmp_path / "test.c"
        src.write_text("void foo() { bar(); }")
        ctags_output = (
            '{"_type": "tag", "name": "foo", "line": 1, "kind": "function", "end": 3}\n'
            '{"_type": "ptag", "name": "!_TAG"}\n'
            '{"_type": "tag", "name": "bar", "line": 2, "kind": "function", "end": 4}\n'
        )
        mock_result = MagicMock(stdout=ctags_output, returncode=0)
        with patch("claudit.skills.index.indexer._check_ctags", return_value="/usr/bin/ctags"), \
             patch("subprocess.run", return_value=mock_result):
            tags = get_ctags_tags(str(src))
        assert len(tags) == 2
        assert tags[0]["name"] == "foo"
        assert tags[1]["name"] == "bar"

    def test_skips_invalid_json(self, tmp_path):
        src = tmp_path / "test.c"
        src.write_text("void foo() {}")
        mock_result = MagicMock(
            stdout='not json\n{"_type": "tag", "name": "foo", "line": 1, "kind": "function"}\n',
            returncode=0,
        )
        with patch("claudit.skills.index.indexer._check_ctags", return_value="/usr/bin/ctags"), \
             patch("subprocess.run", return_value=mock_result):
            tags = get_ctags_tags(str(src))
        assert len(tags) == 1


class TestCtagsFunctionBounds:
    def test_exact_match(self):
        tags = [{"_type": "tag", "name": "foo", "line": 1, "kind": "function", "end": 3}]
        with patch("claudit.skills.index.indexer.get_ctags_tags", return_value=tags):
            assert _ctags_function_bounds("file.c", "foo", 1) == (1, 3)

    def test_fallback_by_name(self):
        tags = [{"_type": "tag", "name": "foo", "line": 5, "kind": "function", "end": 10}]
        with patch("claudit.skills.index.indexer.get_ctags_tags", return_value=tags):
            assert _ctags_function_bounds("file.c", "foo", 1) == (5, 10)

    def test_returns_none_when_no_match(self):
        tags = [{"_type": "tag", "name": "bar", "line": 1, "kind": "function", "end": 3}]
        with patch("claudit.skills.index.indexer.get_ctags_tags", return_value=tags):
            assert _ctags_function_bounds("file.c", "foo", 1) is None

    def test_returns_none_when_no_end(self):
        tags = [{"_type": "tag", "name": "foo", "line": 1, "kind": "function"}]
        with patch("claudit.skills.index.indexer.get_ctags_tags", return_value=tags):
            assert _ctags_function_bounds("file.c", "foo", 1) is None


class TestGetFunctionBody:
    def test_extracts_body(self, tmp_path):
        src = tmp_path / "main.c"
        src.write_text("void foo() {\n    bar();\n}\nvoid other() {\n    baz();\n}\n")
        func = FunctionDef(name="foo", file="main.c", line=1)
        with patch("claudit.skills.index.indexer._ctags_function_bounds", return_value=(1, 3)):
            body = get_function_body(func, str(tmp_path), "c")
        assert body is not None
        assert body.start_line == 1
        assert body.end_line == 3
        assert "bar();" in body.source
        assert "baz" not in body.source

    def test_missing_file_returns_none(self, tmp_path):
        func = FunctionDef(name="foo", file="nope.c", line=1)
        assert get_function_body(func, str(tmp_path), "c") is None

    def test_no_bounds_returns_none(self, tmp_path):
        (tmp_path / "main.c").write_text("void foo() { bar(); }")
        func = FunctionDef(name="foo", file="main.c", line=1)
        with patch("claudit.skills.index.indexer._ctags_function_bounds", return_value=None):
            assert get_function_body(func, str(tmp_path), "c") is None


class TestErrorClasses:
    def test_global_not_found(self):
        with patch("shutil.which", return_value=None):
            with pytest.raises(GlobalNotFoundError, match="GNU Global"):
                from claudit.skills.index.indexer import _check_global
                _check_global()

    def test_ctags_not_found(self):
        with patch("shutil.which", return_value=None):
            with pytest.raises(CtagsNotFoundError, match="Universal Ctags"):
                from claudit.skills.index.indexer import _check_ctags
                _check_ctags()
