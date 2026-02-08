"""Tests for the indexer module (body extraction logic)."""

from claudit.skills.reachability.indexer import (
    FunctionDef,
    _extract_brace_body,
    _extract_indent_body,
)


class TestBraceBody:
    def test_simple_function(self):
        lines = [
            "void foo() {",
            "    bar();",
            "}",
        ]
        body = _extract_brace_body(lines, 0, "test.c")
        assert body.start_line == 1
        assert body.end_line == 3
        assert "bar();" in body.source

    def test_nested_braces(self):
        lines = [
            "void foo() {",
            "    if (x) {",
            "        bar();",
            "    }",
            "}",
        ]
        body = _extract_brace_body(lines, 0, "test.c")
        assert body.start_line == 1
        assert body.end_line == 5

    def test_function_on_multiple_lines(self):
        lines = [
            "void foo(int a,",
            "         int b) {",
            "    bar();",
            "}",
        ]
        body = _extract_brace_body(lines, 0, "test.c")
        assert body.end_line == 4


class TestIndentBody:
    def test_simple_function(self):
        lines = [
            "def foo():",
            "    bar()",
            "    baz()",
            "",
            "def other():",
        ]
        body = _extract_indent_body(lines, 0, "test.py")
        assert body.start_line == 1
        assert "bar()" in body.source
        assert "baz()" in body.source
        assert "other" not in body.source

    def test_nested_function(self):
        lines = [
            "def outer():",
            "    def inner():",
            "        pass",
            "    inner()",
            "",
            "def other():",
        ]
        body = _extract_indent_body(lines, 0, "test.py")
        assert body.start_line == 1
        assert "inner()" in body.source

    def test_multiline_def(self):
        lines = [
            "def foo(a,",
            "        b,",
            "        c):",
            "    return a + b + c",
            "",
            "def other():",
        ]
        body = _extract_indent_body(lines, 0, "test.py")
        assert "return a + b + c" in body.source


class TestCacheModule:
    def test_project_hash_deterministic(self):
        from claudit.skills.reachability.cache import _project_hash

        h1 = _project_hash("/some/path")
        h2 = _project_hash("/some/path")
        assert h1 == h2

    def test_different_paths_different_hashes(self):
        from claudit.skills.reachability.cache import _project_hash

        h1 = _project_hash("/path/a")
        h2 = _project_hash("/path/b")
        assert h1 != h2
