"""Tests for signature extraction."""

import pytest
from claudit.skills.harness.signature_extractor import (
    _parse_c_parameters,
    _parse_java_parameters,
    _parse_python_parameters,
    Parameter,
)


class TestCParameterParsing:
    """Test C parameter parsing."""

    def test_empty_params(self):
        params = _parse_c_parameters("()")
        assert params == []

    def test_void_params(self):
        params = _parse_c_parameters("(void)")
        assert params == []

    def test_single_param(self):
        params = _parse_c_parameters("(int x)")
        assert len(params) == 1
        assert params[0].name == "x"
        assert params[0].type == "int"

    def test_multiple_params(self):
        params = _parse_c_parameters("(int x, char *y)")
        assert len(params) == 2
        assert params[0].name == "x"
        assert params[0].type == "int"
        assert params[1].name == "y"
        assert params[1].type == "char"

    def test_pointer_params(self):
        params = _parse_c_parameters("(void *ptr)")
        assert len(params) == 1
        assert params[0].name == "ptr"
        assert params[0].type == "void"


class TestJavaParameterParsing:
    """Test Java parameter parsing."""

    def test_empty_params(self):
        params = _parse_java_parameters("()")
        assert params == []

    def test_single_param(self):
        params = _parse_java_parameters("(int x)")
        assert len(params) == 1
        assert params[0].name == "x"
        assert params[0].type == "int"

    def test_multiple_params(self):
        params = _parse_java_parameters("(String name, int age)")
        assert len(params) == 2
        assert params[0].name == "name"
        assert params[0].type == "String"
        assert params[1].name == "age"
        assert params[1].type == "int"


class TestPythonParameterParsing:
    """Test Python parameter parsing."""

    def test_empty_params(self):
        params = _parse_python_parameters("()")
        assert params == []

    def test_single_param(self):
        params = _parse_python_parameters("(x)")
        assert len(params) == 1
        assert params[0].name == "x"

    def test_multiple_params(self):
        params = _parse_python_parameters("(x, y, z)")
        assert len(params) == 3
        assert params[0].name == "x"
        assert params[1].name == "y"
        assert params[2].name == "z"

    def test_params_with_defaults(self):
        params = _parse_python_parameters("(x, y=5, z='test')")
        assert len(params) == 3
        assert params[0].name == "x"
        assert params[1].name == "y"
        assert params[2].name == "z"

    def test_params_with_types(self):
        params = _parse_python_parameters("(x: int, y: str)")
        assert len(params) == 2
        assert params[0].name == "x"
        assert params[1].name == "y"

    def test_special_params(self):
        params = _parse_python_parameters("(self, *args, **kwargs)")
        assert len(params) == 3
        assert params[0].name == "self"
        assert params[1].name == "*args"
        assert params[2].name == "**kwargs"
