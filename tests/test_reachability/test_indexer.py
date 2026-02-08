"""Tests for the indexer module (ctags-based body extraction)."""

import textwrap

from claudit.skills.reachability.indexer import (
    FunctionDef,
    get_ctags_tags,
    get_function_body,
)


class TestCtagsTags:
    """Verify ctags --output-format=json --fields=+ne produces usable output."""

    def test_c_function_has_end(self, tmp_path):
        src = tmp_path / "test.c"
        src.write_text(textwrap.dedent("""\
            void foo() {
                bar();
            }
        """))
        tags = get_ctags_tags(str(src))
        foo_tags = [t for t in tags if t["name"] == "foo"]
        assert len(foo_tags) == 1
        assert foo_tags[0]["line"] == 1
        assert "end" in foo_tags[0]
        assert foo_tags[0]["end"] == 3

    def test_c_nested_braces(self, tmp_path):
        src = tmp_path / "test.c"
        src.write_text(textwrap.dedent("""\
            void foo() {
                if (x) {
                    bar();
                }
            }
        """))
        tags = get_ctags_tags(str(src))
        foo = [t for t in tags if t["name"] == "foo"][0]
        assert foo["line"] == 1
        assert foo["end"] == 5

    def test_python_function_has_end(self, tmp_path):
        src = tmp_path / "test.py"
        src.write_text(textwrap.dedent("""\
            def foo():
                bar()
                baz()

            def other():
                pass
        """))
        tags = get_ctags_tags(str(src))
        foo = [t for t in tags if t["name"] == "foo"][0]
        assert foo["line"] == 1
        assert "end" in foo
        # end should cover bar() and baz() but not other()
        assert foo["end"] <= 4

    def test_java_method_has_end(self, tmp_path):
        src = tmp_path / "Test.java"
        src.write_text(textwrap.dedent("""\
            public class Test {
                void foo() {
                    bar();
                }
            }
        """))
        tags = get_ctags_tags(str(src))
        foo = [t for t in tags if t["name"] == "foo"][0]
        assert foo["line"] == 2
        assert "end" in foo
        assert foo["end"] == 4


class TestGetFunctionBody:
    """Test get_function_body using real ctags for bounds."""

    def test_c_simple(self, tmp_path):
        src = tmp_path / "main.c"
        src.write_text(textwrap.dedent("""\
            void foo() {
                bar();
            }
            void other() {
                baz();
            }
        """))
        func = FunctionDef(name="foo", file="main.c", line=1)
        body = get_function_body(func, str(tmp_path), "c")
        assert body is not None
        assert body.start_line == 1
        assert body.end_line == 3
        assert "bar();" in body.source
        assert "baz" not in body.source

    def test_python_simple(self, tmp_path):
        src = tmp_path / "app.py"
        src.write_text(textwrap.dedent("""\
            def foo():
                bar()
                baz()

            def other():
                pass
        """))
        func = FunctionDef(name="foo", file="app.py", line=1)
        body = get_function_body(func, str(tmp_path), "python")
        assert body is not None
        assert "bar()" in body.source
        assert "baz()" in body.source
        assert "other" not in body.source

    def test_missing_file_returns_none(self, tmp_path):
        func = FunctionDef(name="foo", file="nope.c", line=1)
        body = get_function_body(func, str(tmp_path), "c")
        assert body is None


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
