"""Additional tests for index skill API — covers get_body, lookup edge cases, _require_index."""

from unittest.mock import patch, MagicMock

import pytest

from claudit.errors import IndexNotFoundError
from claudit.skills.index import create, get_body, lookup, _require_index
from claudit.skills.index.indexer import FunctionDef, FunctionBody


class TestRequireIndex:
    """Test the internal _require_index helper."""

    def test_auto_index_true_calls_ensure(self, tmp_path):
        with patch("claudit.skills.index._ensure_index") as mock_ensure:
            _require_index(str(tmp_path), auto_index=True)
        mock_ensure.assert_called_once()

    def test_auto_index_false_with_gtags_present(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        # Should not raise
        _require_index(str(tmp_path), auto_index=False)

    def test_auto_index_false_without_gtags_raises(self, tmp_path):
        with pytest.raises(IndexNotFoundError, match="No index found"):
            _require_index(str(tmp_path), auto_index=False)


class TestGetBody:
    """Test get_body with realistic scenarios."""

    def test_returns_body_dict(self, tmp_path):
        """get_body returns full dict with source, file, lines."""
        (tmp_path / "GTAGS").write_text("fake")
        func_def = FunctionDef(name="helper", file="util.c", line=3)
        body = FunctionBody(
            file="util.c", start_line=3, end_line=5,
            source="void helper(int x) {\n    /* work */\n}",
        )

        with patch("claudit.skills.index._find_definition", return_value=[func_def]), \
             patch("claudit.skills.index._get_function_body", return_value=body), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = get_body(str(tmp_path), "helper")

        assert result is not None
        assert result["function"] == "helper"
        assert result["file"] == "util.c"
        assert result["start_line"] == 3
        assert result["end_line"] == 5
        assert "void helper" in result["source"]
        assert result["language"] == "c"

    def test_returns_none_when_no_definition(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        with patch("claudit.skills.index._find_definition", return_value=[]), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = get_body(str(tmp_path), "nonexistent")
        assert result is None

    def test_returns_none_when_no_body(self, tmp_path):
        """get_body returns None when ctags can't find bounds."""
        (tmp_path / "GTAGS").write_text("fake")
        func_def = FunctionDef(name="forward_decl", file="header.h", line=1)

        with patch("claudit.skills.index._find_definition", return_value=[func_def]), \
             patch("claudit.skills.index._get_function_body", return_value=None), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = get_body(str(tmp_path), "forward_decl")
        assert result is None

    def test_explicit_language(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        func_def = FunctionDef(name="main", file="app.py", line=1)
        body = FunctionBody(file="app.py", start_line=1, end_line=3, source="def main():\n    pass")

        with patch("claudit.skills.index._find_definition", return_value=[func_def]), \
             patch("claudit.skills.index._get_function_body", return_value=body):
            result = get_body(str(tmp_path), "main", language="python")

        assert result["language"] == "python"


class TestLookup:
    """Test lookup with different kind parameters."""

    def test_both_kinds(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        defs = [FunctionDef(name="foo", file="main.c", line=10)]
        refs = [FunctionDef(name="foo", file="test.c", line=20),
                FunctionDef(name="foo", file="util.c", line=30)]

        with patch("claudit.skills.index._find_definition", return_value=defs), \
             patch("claudit.skills.index._find_references", return_value=refs):
            result = lookup(str(tmp_path), "foo", kind="both")

        assert len(result["definitions"]) == 1
        assert len(result["references"]) == 2
        assert result["symbol"] == "foo"
        assert result["definitions"][0]["file"] == "main.c"
        assert result["references"][0]["file"] == "test.c"

    def test_references_only(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        refs = [FunctionDef(name="bar", file="caller.c", line=15)]

        with patch("claudit.skills.index._find_references", return_value=refs):
            result = lookup(str(tmp_path), "bar", kind="references")

        assert "definitions" not in result
        assert len(result["references"]) == 1

    def test_no_results(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        with patch("claudit.skills.index._find_definition", return_value=[]), \
             patch("claudit.skills.index._find_references", return_value=[]):
            result = lookup(str(tmp_path), "unknown", kind="both")

        assert result["definitions"] == []
        assert result["references"] == []


class TestCreate:
    """Additional create tests."""

    def test_create_new_index(self, tmp_path):
        """Create index in a directory without existing GTAGS."""
        mock_result = MagicMock(returncode=0, stderr="")
        with patch("claudit.skills.index.indexer._check_gtags", return_value="/usr/bin/gtags"), \
             patch("subprocess.run", return_value=mock_result):
            result = create(str(tmp_path))

        assert result["status"] == "created"
