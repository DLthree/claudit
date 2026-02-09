"""Tests for the call graph caching layer."""

from unittest.mock import patch

from claudit.skills.graph.cache import (
    load_call_graph,
    save_call_graph,
    load_global_results,
    save_global_results,
    _project_hash,
    _cache_dir,
    _cache_key,
)


class TestCallGraphCache:
    def test_roundtrip(self, tmp_path):
        project_dir = str(tmp_path)
        graph = {"a": ["b", "c"], "b": ["d"]}
        with patch("claudit.skills.graph.cache.gtags_mtime", return_value=100.0):
            save_call_graph(project_dir, graph)
            assert load_call_graph(project_dir) == graph

    def test_stale_cache_returns_none(self, tmp_path):
        project_dir = str(tmp_path)
        with patch("claudit.skills.graph.cache.gtags_mtime", return_value=100.0):
            save_call_graph(project_dir, {"a": ["b"]})
        with patch("claudit.skills.graph.cache.gtags_mtime", return_value=200.0):
            assert load_call_graph(project_dir) is None

    def test_no_cache_returns_none(self, tmp_path):
        with patch("claudit.skills.graph.cache.gtags_mtime", return_value=0.0):
            assert load_call_graph(str(tmp_path)) is None


class TestGlobalResultsCache:
    def test_roundtrip(self, tmp_path):
        project_dir = str(tmp_path)
        results = {"symbols": ["foo", "bar"]}
        with patch("claudit.skills.graph.cache.gtags_mtime", return_value=100.0):
            save_global_results(project_dir, results)
            assert load_global_results(project_dir) == results

    def test_stale_returns_none(self, tmp_path):
        project_dir = str(tmp_path)
        with patch("claudit.skills.graph.cache.gtags_mtime", return_value=100.0):
            save_global_results(project_dir, {"symbols": ["foo"]})
        with patch("claudit.skills.graph.cache.gtags_mtime", return_value=200.0):
            assert load_global_results(project_dir) is None


class TestCacheHelpers:
    def test_hash_deterministic(self):
        assert _project_hash("/some/path") == _project_hash("/some/path")

    def test_different_paths_different_hashes(self):
        assert _project_hash("/path/a") != _project_hash("/path/b")

    def test_hash_is_hex_16_chars(self):
        h = _project_hash("/some/path")
        assert len(h) == 16
        int(h, 16)  # should not raise

    def test_cache_dir_under_project(self, tmp_path):
        d = _cache_dir(str(tmp_path))
        assert d.parent.parent == tmp_path.resolve()
        assert d.parent.name == ".cache"

    def test_cache_key_includes_mtime(self, tmp_path):
        with patch("claudit.skills.graph.cache.gtags_mtime", return_value=42.0):
            key = _cache_key(str(tmp_path))
        assert "42.0" in key
