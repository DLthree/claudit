"""Tests for stub generation."""

import pytest
from claudit.skills.harness.stubber import (
    _infer_c_default_return,
    _infer_java_default_return,
    _create_minimal_stub,
)


class TestCDefaultReturns:
    """Test C default return value inference."""

    def test_void_returns_none(self):
        assert _infer_c_default_return("void") is None

    def test_int_returns_zero(self):
        assert _infer_c_default_return("int") == "0"

    def test_long_returns_zero(self):
        assert _infer_c_default_return("long") == "0"

    def test_pointer_returns_null(self):
        assert _infer_c_default_return("char *") == "NULL"
        assert _infer_c_default_return("void *") == "NULL"
        assert _infer_c_default_return("struct foo *") == "NULL"

    def test_float_returns_zero_point_zero(self):
        assert _infer_c_default_return("float") == "0.0"
        assert _infer_c_default_return("double") == "0.0"

    def test_bool_returns_false(self):
        assert _infer_c_default_return("bool") == "false"

    def test_struct_returns_initializer(self):
        result = _infer_c_default_return("struct foo")
        assert "struct foo" in result
        assert "{0}" in result


class TestJavaDefaultReturns:
    """Test Java default return value inference."""

    def test_void_returns_none(self):
        assert _infer_java_default_return("void") is None

    def test_int_returns_zero(self):
        assert _infer_java_default_return("int") == "0"

    def test_long_returns_zero_l(self):
        assert _infer_java_default_return("long") == "0L"

    def test_boolean_returns_false(self):
        assert _infer_java_default_return("boolean") == "false"

    def test_float_returns_zero_f(self):
        assert _infer_java_default_return("float") == "0.0f"

    def test_double_returns_zero_point_zero(self):
        assert _infer_java_default_return("double") == "0.0"

    def test_object_returns_null(self):
        assert _infer_java_default_return("String") == "null"
        assert _infer_java_default_return("Object") == "null"
        assert _infer_java_default_return("MyClass") == "null"


class TestMinimalStub:
    """Test minimal stub generation."""

    def test_c_minimal_stub(self):
        stub = _create_minimal_stub("unknown_func", "c")
        assert stub.name == "unknown_func"
        assert "void" in stub.signature
        assert "AUTO-GENERATED STUB" in stub.stub_source

    def test_java_minimal_stub(self):
        stub = _create_minimal_stub("unknown_func", "java")
        assert stub.name == "unknown_func"
        assert "void" in stub.signature
        assert "AUTO-GENERATED STUB" in stub.stub_source

    def test_python_minimal_stub(self):
        stub = _create_minimal_stub("unknown_func", "python")
        assert stub.name == "unknown_func"
        assert "def" in stub.signature
        assert "AUTO-GENERATED STUB" in stub.stub_source
