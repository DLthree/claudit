"""Tests for the BFS path finder."""

from claudit.skills.reachability.pathfinder import find_all_paths


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
