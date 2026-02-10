"""Tests for full signature extraction pipeline.

These tests exercise extract_signature and language-specific parsers
(_parse_c_signature, _parse_java_signature, _parse_python_signature)
by providing realistic ctags tag dicts and source files.
"""

from unittest.mock import patch

import pytest

from claudit.skills.harness.signature_extractor import (
    extract_signature,
    _parse_c_signature,
    _parse_java_signature,
    _parse_python_signature,
    _parse_generic_signature,
    _extract_c_return_type,
    FunctionSignature,
    Parameter,
)


# ---------------------------------------------------------------------------
# extract_signature — top-level dispatch
# ---------------------------------------------------------------------------
class TestExtractSignature:
    """Test the top-level extract_signature function."""

    def test_c_function(self):
        tags = [
            {
                "_type": "tag",
                "name": "process",
                "line": 3,
                "kind": "function",
                "signature": "(int x, char *buf)",
                "typeref": "typename:int",
            }
        ]
        with patch("claudit.skills.harness.signature_extractor.get_ctags_tags", return_value=tags):
            sig = extract_signature("/project/main.c", "process", "c")

        assert sig is not None
        assert sig.name == "process"
        assert sig.return_type == "int"
        assert len(sig.parameters) == 2
        assert sig.parameters[0].name == "x"
        assert sig.parameters[0].type == "int"

    def test_java_method(self):
        tags = [
            {
                "_type": "tag",
                "name": "getValue",
                "line": 10,
                "kind": "method",
                "signature": "(String key, int default)",
                "typeref": "typename:String",
                "class": "Config",
            }
        ]
        with patch("claudit.skills.harness.signature_extractor.get_ctags_tags", return_value=tags):
            sig = extract_signature("/project/Config.java", "getValue", "java")

        assert sig is not None
        assert sig.name == "getValue"
        assert sig.return_type == "String"
        assert sig.is_method is True
        assert sig.class_name == "Config"
        assert len(sig.parameters) == 2

    def test_python_function(self):
        tags = [
            {
                "_type": "tag",
                "name": "compute",
                "line": 5,
                "kind": "def",
                "signature": "(x, y=0)",
            }
        ]
        with patch("claudit.skills.harness.signature_extractor.get_ctags_tags", return_value=tags):
            sig = extract_signature("/project/app.py", "compute", "python")

        assert sig is not None
        assert sig.name == "compute"
        assert sig.return_type == ""  # Python: no type info from ctags
        assert len(sig.parameters) == 2
        assert sig.parameters[0].name == "x"
        assert sig.parameters[1].name == "y"

    def test_unknown_language_fallback(self):
        tags = [
            {
                "_type": "tag",
                "name": "init",
                "line": 1,
                "kind": "function",
                "signature": "()",
            }
        ]
        with patch("claudit.skills.harness.signature_extractor.get_ctags_tags", return_value=tags):
            sig = extract_signature("/project/file.rs", "init", "rust")

        assert sig is not None
        assert sig.full_signature == "init()"

    def test_returns_none_when_not_found(self):
        tags = [
            {"_type": "tag", "name": "other", "line": 1, "kind": "function"},
        ]
        with patch("claudit.skills.harness.signature_extractor.get_ctags_tags", return_value=tags):
            sig = extract_signature("/project/main.c", "nonexistent", "c")

        assert sig is None

    def test_skips_non_function_tags(self):
        """A variable tag with the same name should be skipped."""
        tags = [
            {"_type": "tag", "name": "data", "line": 1, "kind": "variable"},
            {
                "_type": "tag",
                "name": "data",
                "line": 5,
                "kind": "function",
                "signature": "(int n)",
                "typeref": "typename:void",
            },
        ]
        with patch("claudit.skills.harness.signature_extractor.get_ctags_tags", return_value=tags):
            sig = extract_signature("/project/main.c", "data", "c")

        assert sig is not None
        assert sig.name == "data"
        assert sig.return_type == "void"


# ---------------------------------------------------------------------------
# _parse_c_signature
# ---------------------------------------------------------------------------
class TestParseCSignature:
    def test_with_typeref(self):
        tag = {
            "name": "calculate",
            "signature": "(double a, double b)",
            "typeref": "typename:double",
        }
        sig = _parse_c_signature(tag, "/project/math.c")
        assert sig.return_type == "double"
        assert sig.name == "calculate"
        assert len(sig.parameters) == 2
        assert sig.parameters[0].type == "double"
        assert sig.parameters[0].name == "a"
        assert sig.is_method is False
        assert "double calculate" in sig.full_signature

    def test_without_typeref_reads_source(self, tmp_path):
        """When typeref is absent, return type is parsed from source line."""
        src_file = tmp_path / "util.c"
        src_file.write_text("static int helper(int x) {\n    return x;\n}\n")
        tag = {
            "name": "helper",
            "signature": "(int x)",
            "line": 1,
        }
        sig = _parse_c_signature(tag, str(src_file))
        assert sig.return_type == "int"

    def test_void_params(self):
        tag = {"name": "init", "signature": "(void)", "typeref": "typename:void"}
        sig = _parse_c_signature(tag, "/project/init.c")
        assert sig.parameters == []

    def test_pointer_return(self):
        tag = {
            "name": "create",
            "signature": "(int size)",
            "typeref": "typename:char *",
        }
        sig = _parse_c_signature(tag, "/f.c")
        assert sig.return_type == "char *"


# ---------------------------------------------------------------------------
# _parse_java_signature
# ---------------------------------------------------------------------------
class TestParseJavaSignature:
    def test_instance_method(self):
        tag = {
            "name": "processData",
            "signature": "(String input, int count)",
            "typeref": "typename:boolean",
            "class": "DataProcessor",
        }
        sig = _parse_java_signature(tag, "/project/DataProcessor.java")
        assert sig.name == "processData"
        assert sig.return_type == "boolean"
        assert sig.is_method is True
        assert sig.class_name == "DataProcessor"
        assert len(sig.parameters) == 2
        assert sig.parameters[0].type == "String"
        assert sig.parameters[0].name == "input"

    def test_static_method(self):
        tag = {
            "name": "main",
            "signature": "(String[] args)",
            "typeref": "typename:void",
            "class": "App",
            "access": "public static",
        }
        sig = _parse_java_signature(tag, "/project/App.java")
        assert sig.is_static is True
        assert sig.is_method is True

    def test_scope_based_class_name(self):
        """When class key is absent, scope is used for class name."""
        tag = {
            "name": "run",
            "signature": "()",
            "typeref": "typename:void",
            "scope": "com.example.Runner",
        }
        sig = _parse_java_signature(tag, "/project/Runner.java")
        assert sig.is_method is True
        assert sig.class_name == "Runner"

    def test_no_params(self):
        tag = {
            "name": "size",
            "signature": "()",
            "typeref": "typename:int",
        }
        sig = _parse_java_signature(tag, "/f.java")
        assert sig.parameters == []


# ---------------------------------------------------------------------------
# _parse_python_signature
# ---------------------------------------------------------------------------
class TestParsePythonSignature:
    def test_method_with_self(self):
        tag = {
            "name": "update",
            "signature": "(self, key, value)",
            "class": "Cache",
        }
        sig = _parse_python_signature(tag, "/project/cache.py")
        assert sig.name == "update"
        assert sig.is_method is True
        assert sig.class_name == "Cache"
        assert len(sig.parameters) == 3
        assert sig.parameters[0].name == "self"
        assert "def update" in sig.full_signature

    def test_function_with_defaults_and_types(self):
        tag = {
            "name": "connect",
            "signature": "(host: str, port: int = 8080)",
        }
        sig = _parse_python_signature(tag, "/project/net.py")
        assert len(sig.parameters) == 2
        assert sig.parameters[0].name == "host"
        assert sig.parameters[1].name == "port"
        assert sig.return_type == ""

    def test_scope_based_class(self):
        tag = {
            "name": "step",
            "signature": "(self)",
            "scope": "game.Engine",
        }
        sig = _parse_python_signature(tag, "/engine.py")
        assert sig.is_method is True
        assert sig.class_name == "Engine"


# ---------------------------------------------------------------------------
# _parse_generic_signature
# ---------------------------------------------------------------------------
class TestParseGenericSignature:
    def test_minimal_output(self):
        tag = {"name": "init", "signature": "(cfg)"}
        sig = _parse_generic_signature(tag, "/file.go")
        assert sig.name == "init"
        assert sig.full_signature == "init(cfg)"
        assert sig.parameters == []
        assert sig.is_method is False

    def test_missing_signature(self):
        tag = {"name": "run"}
        sig = _parse_generic_signature(tag, "/file.go")
        assert sig.full_signature == "run()"


# ---------------------------------------------------------------------------
# _extract_c_return_type — parses source file lines
# ---------------------------------------------------------------------------
class TestExtractCReturnType:
    def test_simple_int(self, tmp_path):
        f = tmp_path / "test.c"
        f.write_text("int helper(int x) {\n    return x;\n}\n")
        assert _extract_c_return_type(str(f), 1, "helper") == "int"

    def test_void(self, tmp_path):
        f = tmp_path / "test.c"
        f.write_text("void init() {}\n")
        assert _extract_c_return_type(str(f), 1, "init") == "void"

    def test_static_stripped(self, tmp_path):
        f = tmp_path / "test.c"
        f.write_text("static int calculate(int a, int b) {\n    return a + b;\n}\n")
        assert _extract_c_return_type(str(f), 1, "calculate") == "int"

    def test_line_out_of_range(self, tmp_path):
        f = tmp_path / "test.c"
        f.write_text("int x;\n")
        assert _extract_c_return_type(str(f), 999, "foo") == "void"

    def test_line_zero(self, tmp_path):
        f = tmp_path / "test.c"
        f.write_text("int x;\n")
        assert _extract_c_return_type(str(f), 0, "foo") == "void"

    def test_missing_file(self):
        assert _extract_c_return_type("/nonexistent/file.c", 1, "foo") == "void"

    def test_name_not_in_line(self, tmp_path):
        f = tmp_path / "test.c"
        f.write_text("int other_func(void) {}\n")
        assert _extract_c_return_type(str(f), 1, "missing") == "void"
