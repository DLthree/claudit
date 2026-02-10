"""Tests for dependency analysis — pure functions, no mocking needed.

analyze_dependencies and _is_stdlib_function operate on in-memory dicts
and sets, so they can be tested with realistic call-graph structures
without subprocess mocking.
"""

from claudit.skills.harness.dependency_analyzer import (
    analyze_dependencies,
    _is_stdlib_function,
    DependencySet,
)


# ---------------------------------------------------------------------------
# _is_stdlib_function — pure heuristic
# ---------------------------------------------------------------------------
class TestIsStdlibFunction:
    """Test the stdlib-detection heuristic across C, Java, and Python."""

    # C standard library
    def test_c_stdio(self):
        assert _is_stdlib_function("printf") is True
        assert _is_stdlib_function("fprintf") is True
        assert _is_stdlib_function("fopen") is True
        assert _is_stdlib_function("fclose") is True

    def test_c_stdlib(self):
        assert _is_stdlib_function("malloc") is True
        assert _is_stdlib_function("free") is True
        assert _is_stdlib_function("atoi") is True
        assert _is_stdlib_function("qsort") is True

    def test_c_string(self):
        assert _is_stdlib_function("strlen") is True
        assert _is_stdlib_function("strcpy") is True
        assert _is_stdlib_function("memcpy") is True
        assert _is_stdlib_function("memset") is True

    def test_c_math(self):
        assert _is_stdlib_function("sqrt") is True
        assert _is_stdlib_function("pow") is True
        assert _is_stdlib_function("sin") is True

    def test_c_posix(self):
        assert _is_stdlib_function("fork") is True
        assert _is_stdlib_function("getpid") is True
        assert _is_stdlib_function("read") is True

    def test_c_ctype(self):
        assert _is_stdlib_function("isalpha") is True
        assert _is_stdlib_function("toupper") is True

    # Java standard library prefixes
    def test_java_stdlib_prefixes(self):
        assert _is_stdlib_function("System.out") is True
        assert _is_stdlib_function("String.valueOf") is True
        assert _is_stdlib_function("Math.abs") is True
        assert _is_stdlib_function("Integer.parseInt") is True
        assert _is_stdlib_function("Thread.sleep") is True

    # Python builtins
    def test_python_builtins(self):
        assert _is_stdlib_function("print") is True
        assert _is_stdlib_function("len") is True
        assert _is_stdlib_function("range") is True
        assert _is_stdlib_function("isinstance") is True
        assert _is_stdlib_function("sorted") is True
        assert _is_stdlib_function("open") is True

    # Not stdlib
    def test_project_function_not_stdlib(self):
        assert _is_stdlib_function("process_data") is False
        assert _is_stdlib_function("my_helper") is False
        assert _is_stdlib_function("init_system") is False

    def test_empty_string(self):
        assert _is_stdlib_function("") is False


# ---------------------------------------------------------------------------
# analyze_dependencies — operates on a dict-based call graph
# ---------------------------------------------------------------------------
class TestAnalyzeDependencies:
    """Test BFS-based dependency analysis with realistic call graphs."""

    def test_simple_one_level(self):
        """A function calls a project function and a stdlib function."""
        graph = {
            "process": ["helper", "printf"],
            "helper": [],
        }
        result = analyze_dependencies(
            "/fake/project",
            extracted_function_names={"process"},
            call_graph=graph,
            stub_depth=1,
        )
        assert "helper" in result.stub_functions
        assert "printf" in result.excluded_stdlib

    def test_callee_already_extracted_not_in_stubs(self):
        """Callees in the extracted set should not appear as stubs."""
        graph = {
            "main": ["process", "helper"],
            "process": ["helper"],
            "helper": [],
        }
        result = analyze_dependencies(
            "/fake/project",
            extracted_function_names={"main", "process"},
            call_graph=graph,
            stub_depth=1,
        )
        # helper is a project function not extracted, should need stubbing
        assert "helper" in result.stub_functions
        # process is already extracted, should NOT appear in stubs
        assert "process" not in result.stub_functions

    def test_stdlib_excluded(self):
        """Standard library functions should be excluded from stubs."""
        graph = {
            "main": ["printf", "malloc", "my_func"],
            "my_func": ["strlen"],
        }
        result = analyze_dependencies(
            "/fake/project",
            extracted_function_names={"main"},
            call_graph=graph,
            stub_depth=1,
        )
        assert "printf" in result.excluded_stdlib
        assert "malloc" in result.excluded_stdlib
        assert "my_func" in result.stub_functions
        # strlen is at depth 2, shouldn't appear with stub_depth=1
        assert "strlen" not in result.excluded_stdlib

    def test_depth_two_traversal(self):
        """With stub_depth=2, should follow callees of stubs."""
        graph = {
            "main": ["process"],
            "process": ["helper"],
            "helper": ["util"],
            "util": [],
        }
        result = analyze_dependencies(
            "/fake/project",
            extracted_function_names={"main"},
            call_graph=graph,
            stub_depth=2,
        )
        assert "process" in result.stub_functions
        assert "helper" in result.stub_functions
        # util is at depth 3 from main (main->process->helper->util)
        # but stub_depth=2 means we go 2 levels from extracted funcs
        # main(depth 0) -> process(depth 1) -> helper(depth 2, at limit)
        # So we find process and helper but NOT util

    def test_depth_zero_finds_nothing(self):
        """With stub_depth=0, no traversal should happen."""
        graph = {
            "main": ["helper", "process"],
        }
        result = analyze_dependencies(
            "/fake/project",
            extracted_function_names={"main"},
            call_graph=graph,
            stub_depth=0,
        )
        assert len(result.stub_functions) == 0
        assert len(result.excluded_stdlib) == 0

    def test_dependency_map_recorded(self):
        """The dependency_map should record caller->callees relationships."""
        graph = {
            "main": ["helper", "init"],
            "helper": ["util"],
        }
        result = analyze_dependencies(
            "/fake/project",
            extracted_function_names={"main"},
            call_graph=graph,
            stub_depth=1,
        )
        assert "main" in result.dependency_map
        assert result.dependency_map["main"] == ["helper", "init"]

    def test_unknown_callee_is_stdlib(self):
        """Callees not in the call graph keys are treated as likely stdlib."""
        graph = {
            "main": ["unknown_external"],
        }
        result = analyze_dependencies(
            "/fake/project",
            extracted_function_names={"main"},
            call_graph=graph,
            stub_depth=1,
        )
        # "unknown_external" is not in graph keys → excluded as stdlib
        assert "unknown_external" in result.excluded_stdlib

    def test_cycle_in_graph(self):
        """BFS should not loop forever on cycles."""
        graph = {
            "a": ["b"],
            "b": ["c"],
            "c": ["a"],  # cycle back to a
        }
        result = analyze_dependencies(
            "/fake/project",
            extracted_function_names={"a"},
            call_graph=graph,
            stub_depth=10,
        )
        assert "b" in result.stub_functions
        assert "c" in result.stub_functions
        # 'a' is extracted, shouldn't be in stubs
        assert "a" not in result.stub_functions

    def test_empty_graph(self):
        """Empty call graph should produce empty results."""
        result = analyze_dependencies(
            "/fake/project",
            extracted_function_names={"main"},
            call_graph={},
            stub_depth=1,
        )
        assert len(result.stub_functions) == 0
        assert len(result.excluded_stdlib) == 0
        assert len(result.excluded_extracted) == 0

    def test_multiple_extracted_functions(self):
        """Multiple extracted functions should all serve as BFS roots."""
        graph = {
            "func_a": ["shared_helper"],
            "func_b": ["shared_helper", "other"],
            "shared_helper": [],
            "other": [],
        }
        result = analyze_dependencies(
            "/fake/project",
            extracted_function_names={"func_a", "func_b"},
            call_graph=graph,
            stub_depth=1,
        )
        assert "shared_helper" in result.stub_functions
        assert "other" in result.stub_functions

    def test_realistic_c_project(self):
        """Simulate a real C project with mixed stdlib and project calls."""
        graph = {
            "main": ["init_config", "run_server", "printf"],
            "init_config": ["parse_args", "malloc", "strcpy"],
            "run_server": ["accept_connection", "fork"],
            "parse_args": ["atoi", "strcmp"],
            "accept_connection": ["socket_bind", "printf"],
            "socket_bind": [],
        }
        result = analyze_dependencies(
            "/fake/project",
            extracted_function_names={"main", "run_server"},
            call_graph=graph,
            stub_depth=1,
        )
        # Direct callees of main and run_server
        assert "init_config" in result.stub_functions
        assert "accept_connection" in result.stub_functions
        assert "printf" in result.excluded_stdlib
        assert "fork" in result.excluded_stdlib


# ---------------------------------------------------------------------------
# filter_stub_functions — requires mocked index.lookup
# ---------------------------------------------------------------------------
class TestFilterStubFunctions:
    """Test filtering of stubs against index lookups."""

    def test_keeps_found_functions(self):
        from unittest.mock import patch
        from claudit.skills.harness.dependency_analyzer import filter_stub_functions

        with patch(
            "claudit.skills.index.lookup",
            return_value={"definitions": [{"name": "helper", "file": "util.c", "line": 5}]},
        ):
            result = filter_stub_functions({"helper"}, "/fake")
        assert "helper" in result

    def test_removes_not_found_functions(self):
        from unittest.mock import patch
        from claudit.skills.harness.dependency_analyzer import filter_stub_functions

        with patch(
            "claudit.skills.index.lookup",
            return_value={"definitions": []},
        ):
            result = filter_stub_functions({"external_fn"}, "/fake")
        assert "external_fn" not in result

    def test_removes_functions_on_lookup_error(self):
        from unittest.mock import patch
        from claudit.skills.harness.dependency_analyzer import filter_stub_functions

        with patch(
            "claudit.skills.index.lookup",
            side_effect=Exception("global not found"),
        ):
            result = filter_stub_functions({"broken_fn"}, "/fake")
        assert "broken_fn" not in result
