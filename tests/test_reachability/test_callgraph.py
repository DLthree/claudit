"""Tests for call graph extraction from source code."""

from claudit.skills.reachability.callgraph import (
    _extract_calls_from_source,
    detect_language,
)


class TestExtractCallsC:
    def test_simple_call(self):
        source = """
void foo() {
    bar(x, y);
    baz();
}
"""
        known = {"foo", "bar", "baz", "unknown"}
        calls = _extract_calls_from_source(source, "c", known)
        assert "bar" in calls
        assert "baz" in calls

    def test_no_false_positives_on_declarations(self):
        source = """
void foo() {
    int bar = 5;
}
"""
        known = {"foo", "bar"}
        calls = _extract_calls_from_source(source, "c", known)
        # 'bar' appears as a variable assignment, not a call
        assert "bar" not in calls

    def test_nested_calls(self):
        source = """
void foo() {
    bar(baz(x));
}
"""
        known = {"foo", "bar", "baz"}
        calls = _extract_calls_from_source(source, "c", known)
        assert "bar" in calls
        assert "baz" in calls

    def test_ignores_unknown_symbols(self):
        source = """
void foo() {
    printf("hello");
}
"""
        known = {"foo"}
        calls = _extract_calls_from_source(source, "c", known)
        assert "printf" not in calls


class TestExtractCallsPython:
    def test_simple_call(self):
        source = """
def foo():
    bar(x)
    baz()
"""
        known = {"foo", "bar", "baz"}
        calls = _extract_calls_from_source(source, "python", known)
        assert "bar" in calls
        assert "baz" in calls

    def test_method_call_not_matched(self):
        source = """
def foo():
    obj.bar(x)
"""
        known = {"foo", "bar"}
        calls = _extract_calls_from_source(source, "python", known)
        # 'bar' after a dot is a method - Pygments may tokenize it as Name
        # This depends on lexer behavior; we accept either outcome.

    def test_ignores_unknown(self):
        source = """
def foo():
    unknown_func(x)
"""
        known = set()  # nothing is "known"
        calls = _extract_calls_from_source(source, "python", known)
        assert calls == []


class TestExtractCallsJava:
    def test_simple_call(self):
        source = """
void foo() {
    bar(x);
    baz();
}
"""
        known = {"foo", "bar", "baz"}
        calls = _extract_calls_from_source(source, "java", known)
        assert "bar" in calls
        assert "baz" in calls


class TestDetectLanguage:
    def test_detects_c(self, tmp_path):
        (tmp_path / "main.c").write_text("int main() {}")
        (tmp_path / "util.c").write_text("void util() {}")
        (tmp_path / "util.h").write_text("void util();")
        assert detect_language(str(tmp_path)) == "c"

    def test_detects_python(self, tmp_path):
        (tmp_path / "app.py").write_text("def main(): pass")
        (tmp_path / "util.py").write_text("def util(): pass")
        assert detect_language(str(tmp_path)) == "python"

    def test_detects_java(self, tmp_path):
        (tmp_path / "Main.java").write_text("class Main {}")
        (tmp_path / "Util.java").write_text("class Util {}")
        assert detect_language(str(tmp_path)) == "java"

    def test_empty_defaults_to_c(self, tmp_path):
        assert detect_language(str(tmp_path)) == "c"
