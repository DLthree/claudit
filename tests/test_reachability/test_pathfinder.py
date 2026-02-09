"""Tests for the BFS path finder."""

from unittest.mock import patch

from claudit.skills.path.pathfinder import (
    find_all_paths,
    annotate_path,
    _read_line,
    Hop,
    CallPath,
)
from claudit.skills.reachability.indexer import FunctionDef


def test_direct_call():
    graph = {"a": ["b"]}
    paths = find_all_paths(graph, "a", "b")
    assert paths == [["a", "b"]]


def test_two_hop():
    graph = {"a": ["b"], "b": ["c"]}
    paths = find_all_paths(graph, "a", "c")
    assert paths == [["a", "b", "c"]]


def test_multiple_paths():
    graph = {"a": ["b", "c"], "b": ["d"], "c": ["d"]}
    paths = find_all_paths(graph, "a", "d")
    assert sorted(paths) == sorted([["a", "b", "d"], ["a", "c", "d"]])


def test_no_path():
    graph = {"a": ["b"], "c": ["d"]}
    paths = find_all_paths(graph, "a", "d")
    assert paths == []


def test_cycle_avoidance():
    graph = {"a": ["b"], "b": ["a", "c"]}
    paths = find_all_paths(graph, "a", "c")
    assert paths == [["a", "b", "c"]]


def test_self_loop():
    graph = {"a": ["a", "b"]}
    paths = find_all_paths(graph, "a", "b")
    assert paths == [["a", "b"]]


def test_same_source_and_target():
    graph = {"a": ["b"]}
    paths = find_all_paths(graph, "a", "a")
    assert paths == [["a"]]


def test_max_depth_limit():
    # Chain: a -> b -> c -> d -> e
    graph = {"a": ["b"], "b": ["c"], "c": ["d"], "d": ["e"]}
    # With max_depth=3, path a->b->c->d->e has 5 nodes, too long
    paths = find_all_paths(graph, "a", "e", max_depth=3)
    assert paths == []
    # With max_depth=5, it should work
    paths = find_all_paths(graph, "a", "e", max_depth=5)
    assert paths == [["a", "b", "c", "d", "e"]]


def test_empty_graph():
    paths = find_all_paths({}, "a", "b")
    assert paths == []


def test_source_not_in_graph():
    graph = {"x": ["y"]}
    paths = find_all_paths(graph, "a", "y")
    assert paths == []


def test_diamond_graph():
    graph = {
        "a": ["b", "c"],
        "b": ["d"],
        "c": ["d"],
        "d": ["e"],
    }
    paths = find_all_paths(graph, "a", "e")
    assert sorted(paths) == sorted([
        ["a", "b", "d", "e"],
        ["a", "c", "d", "e"],
    ])


# ---------------------------------------------------------------------------
# annotate_path
# ---------------------------------------------------------------------------
class TestAnnotatePath:
    def test_annotates_with_definition(self):
        defs = [FunctionDef(name="foo", file="main.c", line=10)]
        with patch(
            "claudit.skills.path.pathfinder.find_definition",
            return_value=defs,
        ), patch(
            "claudit.skills.path.pathfinder._read_line",
            return_value="void foo() {",
        ):
            cp = annotate_path(["foo"], "/proj")
        assert len(cp.hops) == 1
        assert cp.hops[0].function == "foo"
        assert cp.hops[0].file == "main.c"
        assert cp.hops[0].line == 10
        assert cp.hops[0].snippet == "void foo() {"

    def test_annotates_unknown_when_no_def(self):
        with patch(
            "claudit.skills.path.pathfinder.find_definition",
            return_value=[],
        ):
            cp = annotate_path(["unknown_func"], "/proj")
        assert len(cp.hops) == 1
        assert cp.hops[0].file == "<unknown>"
        assert cp.hops[0].line == 0
        assert cp.hops[0].snippet == ""

    def test_multi_hop_annotation(self):
        def mock_find_def(name, proj):
            return [FunctionDef(name=name, file=f"{name}.c", line=1)]

        with patch(
            "claudit.skills.path.pathfinder.find_definition",
            side_effect=mock_find_def,
        ), patch(
            "claudit.skills.path.pathfinder._read_line",
            return_value="code",
        ):
            cp = annotate_path(["a", "b", "c"], "/proj")
        assert len(cp.hops) == 3
        assert cp.hops[0].file == "a.c"
        assert cp.hops[1].file == "b.c"
        assert cp.hops[2].file == "c.c"


# ---------------------------------------------------------------------------
# _read_line
# ---------------------------------------------------------------------------
class TestReadLine:
    def test_reads_correct_line(self, tmp_path):
        f = tmp_path / "test.c"
        f.write_text("line1\n  line2  \nline3\n")
        result = _read_line(str(tmp_path), "test.c", 2)
        assert result == "line2"

    def test_returns_empty_for_missing_file(self, tmp_path):
        result = _read_line(str(tmp_path), "nope.c", 1)
        assert result == ""

    def test_returns_empty_for_out_of_range_line(self, tmp_path):
        f = tmp_path / "test.c"
        f.write_text("only one line")
        result = _read_line(str(tmp_path), "test.c", 999)
        assert result == ""

    def test_returns_empty_for_line_zero(self, tmp_path):
        f = tmp_path / "test.c"
        f.write_text("line1")
        result = _read_line(str(tmp_path), "test.c", 0)
        assert result == ""

    def test_returns_empty_on_os_error(self, tmp_path):
        """If reading the file raises OSError, return empty string."""
        f = tmp_path / "test.c"
        f.write_text("content")
        original_read = type(f).read_text
        with patch.object(type(f), "read_text", side_effect=OSError("disk error")):
            result = _read_line(str(tmp_path), "test.c", 1)
        assert result == ""
