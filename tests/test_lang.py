"""Tests for shared language utilities — no mocking needed."""

import json

from claudit.lang import detect_language, load_overrides, LEXER_MAP, EXT_MAP
from pygments.lexers import CLexer, JavaLexer, PythonLexer


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

    def test_mixed_project_picks_dominant(self, tmp_path):
        (tmp_path / "a.py").write_text("")
        (tmp_path / "b.py").write_text("")
        (tmp_path / "c.py").write_text("")
        (tmp_path / "d.c").write_text("")
        assert detect_language(str(tmp_path)) == "python"


class TestLoadOverrides:
    def test_none_returns_none(self):
        assert load_overrides(None) is None

    def test_missing_file_returns_none(self, tmp_path):
        assert load_overrides(str(tmp_path / "nope.json")) is None

    def test_loads_valid_json(self, tmp_path):
        f = tmp_path / "overrides.json"
        f.write_text(json.dumps({"foo": ["bar", "baz"]}))
        result = load_overrides(str(f))
        assert result == {"foo": ["bar", "baz"]}

    def test_rejects_non_dict(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text(json.dumps(["not", "a", "dict"]))
        assert load_overrides(str(f)) is None


class TestLexerMap:
    def test_has_all_languages(self):
        assert set(LEXER_MAP) == {"c", "java", "python"}

    def test_lexers_are_correct_types(self):
        assert LEXER_MAP["c"] is CLexer
        assert LEXER_MAP["java"] is JavaLexer
        assert LEXER_MAP["python"] is PythonLexer
