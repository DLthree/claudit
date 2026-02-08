"""Tests for the caching layer."""

import json
from pathlib import Path
from unittest.mock import patch

from claudit.skills.reachability.cache import (
    load_call_graph,
    save_call_graph,
    _project_hash,
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
