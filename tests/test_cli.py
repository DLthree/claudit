"""Tests for the CLI entry point."""

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
