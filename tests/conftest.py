"""Shared test fixtures for claudit tests."""

import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def c_project(tmp_path):
    """A minimal C project with real source files."""
    (tmp_path / "main.c").write_text(textwrap.dedent("""\
        #include "util.h"

        void process(int x) {
            helper(x);
        }

        int main(int argc, char **argv) {
            process(argc);
            return 0;
        }
    """))
    (tmp_path / "util.c").write_text(textwrap.dedent("""\
        #include "util.h"

        void helper(int x) {
            /* do something */
        }
    """))
    (tmp_path / "util.h").write_text(textwrap.dedent("""\
        void helper(int x);
        void process(int x);
    """))
    # Fake GTAGS so code thinks the index exists
    (tmp_path / "GTAGS").write_text("fake")
    return tmp_path


@pytest.fixture
def python_project(tmp_path):
    """A minimal Python project with real source files."""
    (tmp_path / "app.py").write_text(textwrap.dedent("""\
        def main():
            result = compute(42)
            return result

        def compute(x):
            return transform(x) + 1
    """))
    (tmp_path / "lib.py").write_text(textwrap.dedent("""\
        def transform(x):
            return x * 2
    """))
    (tmp_path / "GTAGS").write_text("fake")
    return tmp_path


@pytest.fixture
def mock_global():
    """Mock subprocess.run for GNU Global commands only.

    Returns a factory that configures responses for specific global invocations.
    Usage:
        mock_global(definitions={"foo": "main.c:10: ..."}, symbols=["foo", "bar"])
    """
    class GlobalMock:
        def __init__(self):
            self.definitions = {}  # name -> "file:line: code" lines
            self.references = {}   # name -> "file:line: code" lines
            self.symbols = []      # list of symbol names

        def __call__(self, args, **kwargs):
            cmd = args
            if not isinstance(cmd, list) or not cmd:
                return MagicMock(stdout="", returncode=0)

            binary = cmd[0]
            if "global" not in binary and binary != "/usr/bin/global":
                return MagicMock(stdout="", returncode=0)

            # global -d --result=grep NAME
            if "-d" in cmd:
                name = cmd[-1]
                output = self.definitions.get(name, "")
                return MagicMock(stdout=output, returncode=0)

            # global -r --result=grep NAME
            if "-r" in cmd:
                name = cmd[-1]
                output = self.references.get(name, "")
                return MagicMock(stdout=output, returncode=0)

            # global -c ""
            if "-c" in cmd:
                output = "\n".join(self.symbols) + "\n" if self.symbols else ""
                return MagicMock(stdout=output, returncode=0)

            return MagicMock(stdout="", returncode=0)

    return GlobalMock
