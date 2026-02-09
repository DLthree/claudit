"""Tests for the CLI entry point."""

import json
from unittest.mock import patch

from claudit.cli import main


def test_no_args_returns_1():
    assert main([]) == 1


def test_help_does_not_crash(capsys):
    try:
        main(["--help"])
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "claudit" in captured.out


def test_reachability_command(capsys):
    mock_result = {
        "paths": [
            {
                "hops": [
                    {"function": "foo", "file": "main.c", "line": 1, "snippet": "void foo()"},
                    {"function": "bar", "file": "util.c", "line": 5, "snippet": "void bar()"},
                ]
            }
        ],
        "cache_used": False,
    }
    with patch("claudit.cli.find_reachability", return_value=mock_result):
        ret = main(["reachability", "foo", "bar", "/some/project"])

    assert ret == 0
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output == mock_result


def test_reachability_with_options(capsys):
    mock_result = {"paths": [], "cache_used": True}
    with patch("claudit.cli.find_reachability", return_value=mock_result) as mock_fn:
        ret = main([
            "reachability", "src", "tgt", "/proj",
            "--language", "python",
            "--max-depth", "5",
            "--overrides", "/path/to/overrides.json",
        ])

    assert ret == 0
    mock_fn.assert_called_once_with(
        source="src",
        target="tgt",
        project_dir="/proj",
        language="python",
        max_depth=5,
        overrides_path="/path/to/overrides.json",
    )


def test_unknown_command_returns_1():
    # No subcommand provided -> returns 1
    assert main([]) == 1


def test_reachability_help_does_not_crash(capsys):
    try:
        main(["reachability", "--help"])
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "source" in captured.out.lower() or "Source" in captured.out
