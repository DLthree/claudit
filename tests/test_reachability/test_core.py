"""Tests for the core orchestration module."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from claudit.skills.reachability.core import find_reachability, _load_overrides
from claudit.skills.reachability.pathfinder import Hop, CallPath


class TestLoadOverrides:
    def test_none_path_returns_none(self):
        assert _load_overrides(None) is None

    def test_nonexistent_file_returns_none(self, tmp_path):
        assert _load_overrides(str(tmp_path / "nope.json")) is None

    def test_valid_json_dict(self, tmp_path):
        f = tmp_path / "overrides.json"
        f.write_text(json.dumps({"caller": ["callee1", "callee2"]}))
        result = _load_overrides(str(f))
        assert result == {"caller": ["callee1", "callee2"]}

    def test_non_dict_json_returns_none(self, tmp_path):
        f = tmp_path / "overrides.json"
        f.write_text(json.dumps(["not", "a", "dict"]))
        result = _load_overrides(str(f))
        assert result is None


class TestFindReachability:
    def test_uses_cached_graph(self):
        graph = {"main": ["helper"], "helper": ["target"]}
        with patch(
            "claudit.skills.reachability.core.ensure_index"
        ), patch(
            "claudit.skills.reachability.core.detect_language",
            return_value="c",
        ), patch(
            "claudit.skills.reachability.core.load_call_graph",
            return_value=graph,
        ), patch(
            "claudit.skills.reachability.core.find_all_paths",
            return_value=[["main", "helper", "target"]],
        ), patch(
            "claudit.skills.reachability.core.annotate_path",
            return_value=CallPath(
                hops=[
                    Hop(function="main", file="main.c", line=1, snippet="void main()"),
                    Hop(function="helper", file="util.c", line=5, snippet="void helper()"),
                    Hop(function="target", file="target.c", line=10, snippet="void target()"),
                ]
            ),
        ):
            result = find_reachability("main", "target", "/proj")

        assert result["cache_used"] is True
        assert len(result["paths"]) == 1
        assert len(result["paths"][0]["hops"]) == 3
        assert result["paths"][0]["hops"][0]["function"] == "main"

    def test_builds_graph_when_no_cache(self):
        graph = {"a": ["b"]}
        with patch(
            "claudit.skills.reachability.core.ensure_index"
        ), patch(
            "claudit.skills.reachability.core.detect_language",
            return_value="c",
        ), patch(
            "claudit.skills.reachability.core.load_call_graph",
            return_value=None,
        ), patch(
            "claudit.skills.reachability.core.build_call_graph",
            return_value=graph,
        ), patch(
            "claudit.skills.reachability.core.save_call_graph",
        ) as mock_save, patch(
            "claudit.skills.reachability.core.find_all_paths",
            return_value=[["a", "b"]],
        ), patch(
            "claudit.skills.reachability.core.annotate_path",
            return_value=CallPath(
                hops=[
                    Hop(function="a", file="a.c", line=1, snippet="a()"),
                    Hop(function="b", file="b.c", line=2, snippet="b()"),
                ]
            ),
        ):
            result = find_reachability("a", "b", "/proj")

        assert result["cache_used"] is False
        mock_save.assert_called_once()

    def test_language_auto_detection(self):
        with patch(
            "claudit.skills.reachability.core.ensure_index"
        ), patch(
            "claudit.skills.reachability.core.detect_language",
            return_value="python",
        ) as mock_detect, patch(
            "claudit.skills.reachability.core.load_call_graph",
            return_value=None,
        ), patch(
            "claudit.skills.reachability.core.build_call_graph",
            return_value={},
        ), patch(
            "claudit.skills.reachability.core.save_call_graph",
        ), patch(
            "claudit.skills.reachability.core.find_all_paths",
            return_value=[],
        ):
            result = find_reachability("a", "b", "/proj", language=None)

        mock_detect.assert_called_once_with("/proj")
        assert result["paths"] == []

    def test_explicit_language_skips_detection(self):
        with patch(
            "claudit.skills.reachability.core.ensure_index"
        ), patch(
            "claudit.skills.reachability.core.detect_language",
        ) as mock_detect, patch(
            "claudit.skills.reachability.core.load_call_graph",
            return_value=None,
        ), patch(
            "claudit.skills.reachability.core.build_call_graph",
            return_value={},
        ), patch(
            "claudit.skills.reachability.core.save_call_graph",
        ), patch(
            "claudit.skills.reachability.core.find_all_paths",
            return_value=[],
        ):
            result = find_reachability("a", "b", "/proj", language="java")

        mock_detect.assert_not_called()

    def test_overrides_invalidate_cache(self, tmp_path):
        overrides_file = tmp_path / "overrides.json"
        overrides_file.write_text(json.dumps({"a": ["b"]}))

        cached_graph = {"x": ["y"]}
        with patch(
            "claudit.skills.reachability.core.ensure_index"
        ), patch(
            "claudit.skills.reachability.core.detect_language",
            return_value="c",
        ), patch(
            "claudit.skills.reachability.core.load_call_graph",
            return_value=cached_graph,
        ), patch(
            "claudit.skills.reachability.core.build_call_graph",
            return_value={"a": ["b"]},
        ) as mock_build, patch(
            "claudit.skills.reachability.core.save_call_graph",
        ), patch(
            "claudit.skills.reachability.core.find_all_paths",
            return_value=[],
        ):
            result = find_reachability(
                "a", "b", "/proj", overrides_path=str(overrides_file)
            )

        # When overrides are present, cache should not be used even if available
        assert result["cache_used"] is False
        mock_build.assert_called_once()

    def test_no_paths_found(self):
        with patch(
            "claudit.skills.reachability.core.ensure_index"
        ), patch(
            "claudit.skills.reachability.core.load_call_graph",
            return_value=None,
        ), patch(
            "claudit.skills.reachability.core.build_call_graph",
            return_value={},
        ), patch(
            "claudit.skills.reachability.core.save_call_graph",
        ), patch(
            "claudit.skills.reachability.core.find_all_paths",
            return_value=[],
        ):
            result = find_reachability("a", "z", "/proj", language="c")

        assert result["paths"] == []
        assert result["cache_used"] is False
