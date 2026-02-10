"""Additional tests for graph skill API — covers _require_graph and build edge cases."""

from unittest.mock import patch

import pytest

from claudit.errors import GraphNotFoundError
from claudit.skills.graph import _require_graph, build, show, callees, callers


class TestRequireGraph:
    """Test the internal _require_graph helper directly."""

    def test_returns_cached_graph(self, tmp_path):
        graph = {"a": ["b"]}
        with patch("claudit.skills.graph.load_call_graph", return_value=graph):
            result = _require_graph(str(tmp_path), auto_build=True)
        assert result == graph

    def test_auto_builds_when_no_cache(self, tmp_path):
        built_graph = {"x": ["y"]}
        with patch("claudit.skills.graph.load_call_graph", return_value=None), \
             patch("claudit.skills.graph.ensure_index"), \
             patch("claudit.skills.graph.detect_language", return_value="c"), \
             patch("claudit.skills.graph.build_call_graph", return_value=built_graph), \
             patch("claudit.skills.graph.save_call_graph"):
            result = _require_graph(str(tmp_path), auto_build=True)
        assert result == built_graph

    def test_raises_when_no_cache_and_no_auto_build(self, tmp_path):
        with patch("claudit.skills.graph.load_call_graph", return_value=None):
            with pytest.raises(GraphNotFoundError):
                _require_graph(str(tmp_path), auto_build=False)


class TestBuildEdgeCases:
    """Test build() edge cases: overrides, language auto-detection."""

    def test_build_with_overrides(self, tmp_path):
        """Overrides force a rebuild even if cache exists."""
        (tmp_path / "GTAGS").write_text("fake")
        new_graph = {"a": ["b", "c"]}
        overrides_file = tmp_path / "overrides.json"
        overrides_file.write_text('{"a": ["extra"]}')

        with patch("claudit.skills.graph.load_call_graph", return_value={"a": ["b"]}), \
             patch("claudit.skills.graph.build_call_graph", return_value=new_graph), \
             patch("claudit.skills.graph.save_call_graph"), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = build(str(tmp_path), overrides_path=str(overrides_file))

        assert result["status"] == "built"

    def test_build_no_cache_creates(self, tmp_path):
        """When no cache and no force, a fresh build happens."""
        (tmp_path / "GTAGS").write_text("fake")
        new_graph = {"main": ["init"]}

        with patch("claudit.skills.graph.load_call_graph", return_value=None), \
             patch("claudit.skills.graph.build_call_graph", return_value=new_graph), \
             patch("claudit.skills.graph.save_call_graph"), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = build(str(tmp_path))

        assert result["status"] == "built"
        assert result["node_count"] == 1
        assert result["edge_count"] == 1

    def test_build_with_explicit_language(self, tmp_path):
        """Explicit language parameter is used instead of auto-detection."""
        (tmp_path / "GTAGS").write_text("fake")
        new_graph = {"App.main": ["App.run"]}

        with patch("claudit.skills.graph.load_call_graph", return_value=None), \
             patch("claudit.skills.graph.build_call_graph", return_value=new_graph) as mock_build, \
             patch("claudit.skills.graph.save_call_graph"):
            result = build(str(tmp_path), language="java")

        assert result["language"] == "java"


class TestShowEdgeCases:
    def test_edge_count(self, tmp_path):
        graph = {"a": ["b", "c"], "d": ["e"]}
        with patch("claudit.skills.graph._require_graph", return_value=graph):
            result = show(str(tmp_path))
        assert result["edge_count"] == 3
        assert result["node_count"] == 2

    def test_empty_graph(self, tmp_path):
        with patch("claudit.skills.graph._require_graph", return_value={}):
            result = show(str(tmp_path))
        assert result["graph"] == {}
        assert result["node_count"] == 0
        assert result["edge_count"] == 0


class TestCalleesAndCallers:
    def test_callers_returns_sorted(self, tmp_path):
        """Callers should be returned in sorted order."""
        graph = {"z_func": ["target"], "a_func": ["target"], "m_func": ["target"]}
        with patch("claudit.skills.graph._require_graph", return_value=graph):
            result = callers(str(tmp_path), "target")
        assert result["callers"] == ["a_func", "m_func", "z_func"]
        assert result["count"] == 3

    def test_callees_empty_graph(self, tmp_path):
        with patch("claudit.skills.graph._require_graph", return_value={}):
            result = callees(str(tmp_path), "anything")
        assert result["callees"] == []
        assert result["count"] == 0
