"""Tests for the CLI dispatcher."""

import json
from unittest.mock import patch, MagicMock

from claudit.cli import main


class TestCLIDispatch:
    def test_no_command_shows_help(self, capsys):
        ret = main([])
        assert ret == 1
        out = capsys.readouterr().out
        assert "index" in out
        assert "graph" in out

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

    def test_graph_build_cached(self, tmp_path, capsys):
        (tmp_path / "GTAGS").write_text("fake")
        with patch("claudit.skills.graph.load_call_graph", return_value={"a": ["b"]}), \
             patch("claudit.lang.detect_language", return_value="c"):
            ret = main(["graph", "build", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "cached"

    def test_graph_callees(self, tmp_path, capsys):
        with patch("claudit.skills.graph._require_graph", return_value={"main": ["helper"]}):
            ret = main(["graph", "callees", "main", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["callees"] == ["helper"]

    def test_help_lists_all_skills(self, capsys):
        try:
            main(["--help"])
        except SystemExit:
            pass
        out = capsys.readouterr().out
        for skill in ("index", "graph", "path", "highlight"):
            assert skill in out
