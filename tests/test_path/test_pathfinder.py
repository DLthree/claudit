"""Tests for BFS path finding — pure functions, no mocking needed."""

from unittest.mock import patch

from claudit.skills.index.indexer import FunctionDef
from claudit.skills.path.pathfinder import (
    find_all_paths,
    annotate_path,
    _read_line,
)


# ---------------------------------------------------------------------------
# find_all_paths — pure function
# ---------------------------------------------------------------------------
def test_direct_call():
    assert find_all_paths({"a": ["b"]}, "a", "b") == [["a", "b"]]


def test_two_hop():
    assert find_all_paths({"a": ["b"], "b": ["c"]}, "a", "c") == [["a", "b", "c"]]


def test_multiple_paths():
    graph = {"a": ["b", "c"], "b": ["d"], "c": ["d"]}
    paths = find_all_paths(graph, "a", "d")
    assert sorted(paths) == sorted([["a", "b", "d"], ["a", "c", "d"]])


def test_no_path():
    assert find_all_paths({"a": ["b"], "c": ["d"]}, "a", "d") == []


def test_cycle_avoidance():
    graph = {"a": ["b"], "b": ["a", "c"]}
    assert find_all_paths(graph, "a", "c") == [["a", "b", "c"]]


def test_self_loop():
    assert find_all_paths({"a": ["a", "b"]}, "a", "b") == [["a", "b"]]


def test_same_source_and_target():
    assert find_all_paths({"a": ["b"]}, "a", "a") == [["a"]]


def test_max_depth_limit():
    graph = {"a": ["b"], "b": ["c"], "c": ["d"], "d": ["e"]}
    assert find_all_paths(graph, "a", "e", max_depth=3) == []
    assert find_all_paths(graph, "a", "e", max_depth=5) == [["a", "b", "c", "d", "e"]]


def test_empty_graph():
    assert find_all_paths({}, "a", "b") == []


def test_diamond_graph():
    graph = {"a": ["b", "c"], "b": ["d"], "c": ["d"], "d": ["e"]}
    paths = find_all_paths(graph, "a", "e")
    assert sorted(paths) == sorted([["a", "b", "d", "e"], ["a", "c", "d", "e"]])


# ---------------------------------------------------------------------------
# annotate_path — needs mocked Global for find_definition
# ---------------------------------------------------------------------------
class TestAnnotatePath:
    def test_annotates_with_definition(self):
        defs = [FunctionDef(name="foo", file="main.c", line=10)]
        with patch("claudit.skills.path.pathfinder.find_definition", return_value=defs), \
             patch("claudit.skills.path.pathfinder._read_line", return_value="void foo() {"):
            cp = annotate_path(["foo"], "/proj")
        assert len(cp.hops) == 1
        assert cp.hops[0].function == "foo"
        assert cp.hops[0].file == "main.c"
        assert cp.hops[0].line == 10

    def test_unknown_function(self):
        with patch("claudit.skills.path.pathfinder.find_definition", return_value=[]):
            cp = annotate_path(["unknown_func"], "/proj")
        assert cp.hops[0].file == "<unknown>"
        assert cp.hops[0].line == 0


# ---------------------------------------------------------------------------
# _read_line — real file I/O, no mocking needed
# ---------------------------------------------------------------------------
class TestReadLine:
    def test_reads_correct_line(self, tmp_path):
        (tmp_path / "test.c").write_text("line1\n  line2  \nline3\n")
        assert _read_line(str(tmp_path), "test.c", 2) == "line2"

    def test_missing_file(self, tmp_path):
        assert _read_line(str(tmp_path), "nope.c", 1) == ""

    def test_out_of_range(self, tmp_path):
        (tmp_path / "test.c").write_text("only one line")
        assert _read_line(str(tmp_path), "test.c", 999) == ""

    def test_line_zero(self, tmp_path):
        (tmp_path / "test.c").write_text("line1")
        assert _read_line(str(tmp_path), "test.c", 0) == ""
