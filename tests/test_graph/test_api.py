"""Tests for the /graph skill public API."""

from unittest.mock import patch, MagicMock

import pytest

from claudit.errors import GraphNotFoundError
from claudit.skills.graph import build, show, callees, callers


class TestBuild:
    def test_returns_cached_status(self, tmp_path):
        cached_graph = {"a": ["b", "c"]}
        (tmp_path / "GTAGS").write_text("fake")
        with patch("claudit.skills.graph._load_graph", return_value=cached_graph), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = build(str(tmp_path))
        assert result["status"] == "cached"
        assert result["node_count"] == 1
        assert result["edge_count"] == 2

    def test_builds_when_no_cache(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        new_graph = {"x": ["y"]}
        with patch("claudit.skills.graph._load_graph", return_value=None), \
             patch("claudit.skills.graph._build_graph", return_value=new_graph), \
             patch("claudit.skills.graph._save_graph"), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = build(str(tmp_path))
        assert result["status"] == "built"

    def test_force_rebuilds(self, tmp_path):
        (tmp_path / "GTAGS").write_text("fake")
        new_graph = {"x": ["y", "z"]}
        with patch("claudit.skills.graph._load_graph", return_value={"a": ["b"]}), \
             patch("claudit.skills.graph._build_graph", return_value=new_graph), \
             patch("claudit.skills.graph._save_graph"), \
             patch("claudit.lang.detect_language", return_value="c"):
            result = build(str(tmp_path), force=True)
        assert result["status"] == "built"
        assert result["edge_count"] == 2


class TestShow:
    def test_returns_graph(self, tmp_path):
        graph = {"a": ["b"], "c": ["d"]}
        with patch("claudit.skills.graph._require_graph", return_value=graph):
            result = show(str(tmp_path))
        assert result["graph"] == graph
        assert result["node_count"] == 2
        assert result["edge_count"] == 2

    def test_no_auto_build_raises(self, tmp_path):
        with patch("claudit.skills.graph._require_graph", side_effect=GraphNotFoundError("no graph")):
            with pytest.raises(GraphNotFoundError):
                show(str(tmp_path), auto_build=False)


class TestCallees:
    def test_returns_callees(self, tmp_path):
        graph = {"main": ["helper", "init"], "helper": ["util"]}
        with patch("claudit.skills.graph._require_graph", return_value=graph):
            result = callees(str(tmp_path), "main")
        assert result["function"] == "main"
        assert result["callees"] == ["helper", "init"]
        assert result["count"] == 2

    def test_unknown_function_returns_empty(self, tmp_path):
        graph = {"main": ["helper"]}
        with patch("claudit.skills.graph._require_graph", return_value=graph):
            result = callees(str(tmp_path), "nonexistent")
        assert result["callees"] == []
        assert result["count"] == 0


class TestCallers:
    def test_returns_callers(self, tmp_path):
        graph = {"main": ["helper"], "test": ["helper"]}
        with patch("claudit.skills.graph._require_graph", return_value=graph):
            result = callers(str(tmp_path), "helper")
        assert result["function"] == "helper"
        assert sorted(result["callers"]) == ["main", "test"]
        assert result["count"] == 2

    def test_no_callers(self, tmp_path):
        graph = {"main": ["helper"]}
        with patch("claudit.skills.graph._require_graph", return_value=graph):
            result = callers(str(tmp_path), "main")
        assert result["callers"] == []
        assert result["count"] == 0
