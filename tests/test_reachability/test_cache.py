"""Tests for the caching layer."""

import json
from pathlib import Path
from unittest.mock import patch

from claudit.skills.reachability.cache import (
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

        with patch(
            "claudit.skills.reachability.cache.gtags_mtime", return_value=100.0
        ):
            save_call_graph(project_dir, graph)
            loaded = load_call_graph(project_dir)

        assert loaded == graph

    def test_stale_cache_returns_none(self, tmp_path):
        project_dir = str(tmp_path)
        graph = {"a": ["b"]}

        with patch(
            "claudit.skills.reachability.cache.gtags_mtime", return_value=100.0
        ):
            save_call_graph(project_dir, graph)

        # Now GTAGS mtime changed
        with patch(
            "claudit.skills.reachability.cache.gtags_mtime", return_value=200.0
        ):
            loaded = load_call_graph(project_dir)

        assert loaded is None

    def test_no_cache_returns_none(self, tmp_path):
        project_dir = str(tmp_path)
        with patch(
            "claudit.skills.reachability.cache.gtags_mtime", return_value=0.0
        ):
            loaded = load_call_graph(project_dir)
        assert loaded is None


class TestGlobalResultsCache:
    def test_roundtrip(self, tmp_path):
        project_dir = str(tmp_path)
        results = {"symbols": ["foo", "bar"], "defs": {"foo": "main.c:1"}}

        with patch(
            "claudit.skills.reachability.cache.gtags_mtime", return_value=100.0
        ):
            save_global_results(project_dir, results)
            loaded = load_global_results(project_dir)

        assert loaded == results

    def test_stale_cache_returns_none(self, tmp_path):
        project_dir = str(tmp_path)
        results = {"symbols": ["foo"]}

        with patch(
            "claudit.skills.reachability.cache.gtags_mtime", return_value=100.0
        ):
            save_global_results(project_dir, results)

        with patch(
            "claudit.skills.reachability.cache.gtags_mtime", return_value=200.0
        ):
            loaded = load_global_results(project_dir)

        assert loaded is None

    def test_no_cache_returns_none(self, tmp_path):
        project_dir = str(tmp_path)
        with patch(
            "claudit.skills.reachability.cache.gtags_mtime", return_value=0.0
        ):
            loaded = load_global_results(project_dir)
        assert loaded is None


class TestCacheHelpers:
    def test_project_hash_deterministic(self):
        h1 = _project_hash("/some/path")
        h2 = _project_hash("/some/path")
        assert h1 == h2

    def test_different_paths_different_hashes(self):
        h1 = _project_hash("/path/a")
        h2 = _project_hash("/path/b")
        assert h1 != h2

    def test_project_hash_is_hex_16_chars(self):
        h = _project_hash("/some/path")
        assert len(h) == 16
        int(h, 16)  # should not raise

    def test_cache_dir_under_project(self, tmp_path):
        project_dir = str(tmp_path)
        d = _cache_dir(project_dir)
        assert d.parent.parent == tmp_path.resolve()
        assert d.parent.name == ".cache"

    def test_cache_key_includes_mtime(self, tmp_path):
        project_dir = str(tmp_path)
        with patch(
            "claudit.skills.reachability.cache.gtags_mtime", return_value=42.0
        ):
            key = _cache_key(project_dir)
        assert "42.0" in key
        assert _project_hash(project_dir) in key
