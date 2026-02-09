"""Tests for the /index skill public API."""

from unittest.mock import patch, MagicMock

import pytest

from claudit.errors import IndexNotFoundError
from claudit.skills.index import create, list_symbols, get_body, lookup


class TestCreate:
    def test_existing_index_returns_exists(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        result = create(str(tmp_path))
        assert result["status"] == "exists"
        assert result["gtags_mtime"] > 0

    def test_force_rebuild(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        (tmp_path / "GRTAGS").write_text("fake")
        (tmp_path / "GPATH").write_text("fake")
        mock_result = MagicMock(returncode=0, stderr="")
        with patch("claudit.skills.index.indexer._check_gtags", return_value="/usr/bin/gtags"), \
             patch("subprocess.run", return_value=mock_result):
            result = create(str(tmp_path), force=True)
        assert result["status"] == "rebuilt"

    def test_creates_new_index(self, tmp_path):
        mock_result = MagicMock(returncode=0, stderr="")
        with patch("claudit.skills.index.indexer._check_gtags", return_value="/usr/bin/gtags"), \
             patch("subprocess.run", return_value=mock_result):
            result = create(str(tmp_path))
        assert result["status"] == "created"


class TestListSymbols:
    def test_returns_structured_result(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        mock_result = MagicMock(stdout="foo\nbar\n", returncode=0)
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            result = list_symbols(str(tmp_path))
        assert result["symbols"] == ["foo", "bar"]
        assert result["count"] == 2

    def test_no_auto_index_raises_without_gtags(self, tmp_path):
        with pytest.raises(IndexNotFoundError):
            list_symbols(str(tmp_path), auto_index=False)


class TestGetBody:
    def test_returns_body(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        src = tmp_path / "main.c"
        src.write_text("void foo() {\n    bar();\n}\n")
        from claudit.skills.index.indexer import FunctionDef
        mock_def = [FunctionDef(name="foo", file="main.c", line=1)]
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=MagicMock(stdout="main.c:1: void foo() {", returncode=0)), \
             patch("claudit.skills.index.indexer._ctags_function_bounds", return_value=(1, 3)):
            result = get_body(str(tmp_path), "foo", language="c")
        assert result is not None
        assert result["function"] == "foo"
        assert "bar();" in result["source"]

    def test_returns_none_for_unknown(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        mock_result = MagicMock(stdout="", returncode=0)
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            result = get_body(str(tmp_path), "nonexistent", language="c")
        assert result is None


class TestLookup:
    def test_returns_both(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        mock_defs = MagicMock(stdout="main.c:10: int foo(void) {", returncode=0)
        mock_refs = MagicMock(stdout="caller.c:20: foo();", returncode=0)
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", side_effect=[mock_defs, mock_refs]):
            result = lookup(str(tmp_path), "foo")
        assert result["symbol"] == "foo"
        assert len(result["definitions"]) == 1
        assert len(result["references"]) == 1

    def test_definitions_only(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        mock_defs = MagicMock(stdout="main.c:10: int foo(void) {", returncode=0)
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_defs):
            result = lookup(str(tmp_path), "foo", kind="definitions")
        assert "definitions" in result
        assert "references" not in result

    def test_references_only(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        mock_refs = MagicMock(stdout="caller.c:20: foo();", returncode=0)
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_refs):
            result = lookup(str(tmp_path), "foo", kind="references")
        assert "references" in result
        assert "definitions" not in result
