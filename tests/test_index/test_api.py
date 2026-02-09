"""Tests for the /index skill public API."""

from unittest.mock import patch, MagicMock

import pytest

from claudit.errors import IndexNotFoundError
from claudit.skills.index import create, list_symbols, get_body, lookup


class TestCreate:
    def test_existing_index(self, tmp_path):
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
        # Stale files should have been removed before re-indexing
        assert not (tmp_path / "GRTAGS").exists()


class TestListSymbols:
    def test_structured_result(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        mock_result = MagicMock(stdout="foo\nbar\n", returncode=0)
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            result = list_symbols(str(tmp_path))
        assert result["symbols"] == ["foo", "bar"]
        assert result["count"] == 2

    def test_no_auto_index_raises(self, tmp_path):
        with pytest.raises(IndexNotFoundError):
            list_symbols(str(tmp_path), auto_index=False)


class TestLookup:
    def test_definitions_only(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        mock_result = MagicMock(stdout="main.c:10: int foo(void) {", returncode=0)
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            result = lookup(str(tmp_path), "foo", kind="definitions")
        assert result["symbol"] == "foo"
        assert len(result["definitions"]) == 1
        assert "references" not in result
