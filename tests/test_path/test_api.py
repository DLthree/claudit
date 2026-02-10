"""Tests for the /path skill public API (path/__init__.py).

The find() function orchestrates graph loading, BFS path finding, and
annotation.  We mock at the graph/cache boundary and use real BFS logic.
"""

from unittest.mock import patch, MagicMock

import pytest

from claudit.errors import GraphNotFoundError
from claudit.skills.index.indexer import FunctionDef
from claudit.skills.path import find


class TestFindWithCachedGraph:
    """Test find() when a cached call graph is available."""

    def test_finds_direct_path(self):
        """Find a direct call path using cached graph."""
        graph = {"main": ["helper"], "helper": []}

        with patch("claudit.skills.path.load_call_graph", return_value=graph), \
             patch("claudit.skills.path.load_overrides", return_value=None), \
             patch("claudit.skills.path.pathfinder.find_definition", return_value=[]):
            result = find("/project", "main", "helper", annotate=True)

        assert result["source"] == "main"
        assert result["target"] == "helper"
        assert result["path_count"] == 1
        assert result["cache_used"] is True

    def test_finds_multi_hop_path(self):
        """Find a two-hop path: main -> process -> helper."""
        graph = {"main": ["process"], "process": ["helper"], "helper": []}

        with patch("claudit.skills.path.load_call_graph", return_value=graph), \
             patch("claudit.skills.path.load_overrides", return_value=None), \
             patch("claudit.skills.path.pathfinder.find_definition", return_value=[]):
            result = find("/project", "main", "helper", annotate=True)

        assert result["path_count"] == 1
        assert result["paths"][0]["length"] == 3

    def test_no_path_found(self):
        """Return empty paths when no path exists."""
        graph = {"main": ["helper"], "other": ["target"]}

        with patch("claudit.skills.path.load_call_graph", return_value=graph), \
             patch("claudit.skills.path.load_overrides", return_value=None):
            result = find("/project", "main", "target", annotate=False)

        assert result["path_count"] == 0
        assert result["paths"] == []

    def test_unannotated_returns_names_only(self):
        """With annotate=False, paths contain function name lists."""
        graph = {"a": ["b"], "b": ["c"]}

        with patch("claudit.skills.path.load_call_graph", return_value=graph), \
             patch("claudit.skills.path.load_overrides", return_value=None):
            result = find("/project", "a", "c", annotate=False)

        assert result["path_count"] == 1
        path = result["paths"][0]
        assert path["hops"] == ["a", "b", "c"]
        assert path["length"] == 3

    def test_annotated_includes_file_and_line(self):
        """With annotate=True, hops have file, line, and snippet info."""
        graph = {"foo": ["bar"]}
        defs = {"foo": [FunctionDef(name="foo", file="main.c", line=10)],
                "bar": [FunctionDef(name="bar", file="util.c", line=5)]}

        def mock_find_def(name, proj):
            return defs.get(name, [])

        with patch("claudit.skills.path.load_call_graph", return_value=graph), \
             patch("claudit.skills.path.load_overrides", return_value=None), \
             patch("claudit.skills.path.pathfinder.find_definition", side_effect=mock_find_def), \
             patch("claudit.skills.path.pathfinder._read_line", return_value="void foo() {"):
            result = find("/project", "foo", "bar", annotate=True)

        assert result["path_count"] == 1
        hops = result["paths"][0]["hops"]
        assert hops[0]["function"] == "foo"
        assert hops[0]["file"] == "main.c"
        assert hops[0]["line"] == 10

    def test_max_depth_limits_results(self):
        """Paths longer than max_depth are excluded."""
        graph = {"a": ["b"], "b": ["c"], "c": ["d"], "d": ["e"]}

        with patch("claudit.skills.path.load_call_graph", return_value=graph), \
             patch("claudit.skills.path.load_overrides", return_value=None):
            result = find("/project", "a", "e", max_depth=3, annotate=False)

        assert result["path_count"] == 0


class TestFindWithGraphBuilding:
    """Test find() when the graph must be built."""

    def test_auto_builds_when_no_cache(self):
        """When no cached graph exists and auto_build=True, graph is built."""
        built_graph = {"main": ["target"]}

        with patch("claudit.skills.path.load_call_graph", side_effect=[None, built_graph]), \
             patch("claudit.skills.path.load_overrides", return_value=None), \
             patch("claudit.skills.path.build_graph") as mock_build, \
             patch("claudit.skills.path.pathfinder.find_definition", return_value=[]):
            result = find("/project", "main", "target", annotate=True)

        mock_build.assert_called_once()
        assert result["path_count"] == 1
        assert result["cache_used"] is False

    def test_raises_when_no_cache_and_no_auto_build(self):
        """When no graph and auto_build=False, raise GraphNotFoundError."""
        with patch("claudit.skills.path.load_call_graph", return_value=None), \
             patch("claudit.skills.path.load_overrides", return_value=None):
            with pytest.raises(GraphNotFoundError):
                find("/project", "main", "target", auto_build=False)

    def test_forces_rebuild_with_overrides(self):
        """When overrides are provided, graph is always rebuilt."""
        graph = {"main": ["target"]}
        overrides = {"main": ["extra"]}

        with patch("claudit.skills.path.load_call_graph", side_effect=[graph, graph]), \
             patch("claudit.skills.path.load_overrides", return_value=overrides), \
             patch("claudit.skills.path.build_graph") as mock_build, \
             patch("claudit.skills.path.pathfinder.find_definition", return_value=[]):
            result = find("/project", "main", "target", overrides_path="/overrides.json")

        mock_build.assert_called_once()
        assert result["cache_used"] is False

    def test_empty_graph_after_build(self):
        """If build produces nothing, an empty graph is used."""
        with patch("claudit.skills.path.load_call_graph", side_effect=[None, None]), \
             patch("claudit.skills.path.load_overrides", return_value=None), \
             patch("claudit.skills.path.build_graph"):
            result = find("/project", "main", "target", annotate=False)

        assert result["path_count"] == 0


class TestFindMultiplePaths:
    """Test find() with diamond-shaped graphs that produce multiple paths."""

    def test_diamond_graph(self):
        """Diamond: a -> b, a -> c, b -> d, c -> d should find two paths."""
        graph = {"a": ["b", "c"], "b": ["d"], "c": ["d"]}

        with patch("claudit.skills.path.load_call_graph", return_value=graph), \
             patch("claudit.skills.path.load_overrides", return_value=None):
            result = find("/project", "a", "d", annotate=False)

        assert result["path_count"] == 2
        hop_lists = sorted([p["hops"] for p in result["paths"]])
        assert hop_lists == [["a", "b", "d"], ["a", "c", "d"]]
