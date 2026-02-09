"""Tests for the new multi-level CLI dispatch."""

import json
from unittest.mock import patch, MagicMock

from claudit.cli import main


class TestIndexCLI:
    def test_index_create(self, tmp_path, capsys):
        (tmp_path / "GTAGS").write_text("fake")
        ret = main(["index", "create", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "exists"

    def test_index_list_symbols(self, tmp_path, capsys):
        (tmp_path / "GTAGS").write_text("fake")
        mock_result = MagicMock(stdout="foo\nbar\n", returncode=0)
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            ret = main(["index", "list-symbols", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["count"] == 2

    def test_index_lookup(self, tmp_path, capsys):
        (tmp_path / "GTAGS").write_text("fake")
        mock_result = MagicMock(stdout="main.c:10: int foo(void) {", returncode=0)
        with patch("claudit.skills.index.indexer._check_global", return_value="/usr/bin/global"), \
             patch("subprocess.run", return_value=mock_result):
            ret = main(["index", "lookup", "foo", str(tmp_path), "--kind", "definitions"])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["symbol"] == "foo"


class TestGraphCLI:
    def test_graph_build(self, tmp_path, capsys):
        (tmp_path / "GTAGS").write_text("fake")
        cached_graph = {"a": ["b"]}
        with patch("claudit.skills.graph._load_graph", return_value=cached_graph), \
             patch("claudit.lang.detect_language", return_value="c"):
            ret = main(["graph", "build", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "cached"

    def test_graph_callees(self, tmp_path, capsys):
        graph = {"main": ["helper"]}
        with patch("claudit.skills.graph._require_graph", return_value=graph):
            ret = main(["graph", "callees", "main", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["callees"] == ["helper"]

    def test_graph_callers(self, tmp_path, capsys):
        graph = {"main": ["helper"], "test": ["helper"]}
        with patch("claudit.skills.graph._require_graph", return_value=graph):
            ret = main(["graph", "callers", "helper", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert sorted(output["callers"]) == ["main", "test"]


class TestLegacyReachability:
    def test_still_works(self, capsys):
        mock_result = {
            "paths": [{"hops": [{"function": "a", "file": "a.c", "line": 1, "snippet": "a()"}]}],
            "cache_used": False,
        }
        with patch("claudit.cli.find_reachability", return_value=mock_result):
            ret = main(["reachability", "a", "b", "/proj"])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output == mock_result


class TestHelpDoesNotCrash:
    def test_top_level_help(self, capsys):
        try:
            main(["--help"])
        except SystemExit:
            pass
        captured = capsys.readouterr()
        assert "index" in captured.out
        assert "graph" in captured.out
        assert "path" in captured.out

    def test_index_help(self, capsys):
        try:
            main(["index", "--help"])
        except SystemExit:
            pass
        captured = capsys.readouterr()
        assert "create" in captured.out
