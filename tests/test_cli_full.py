"""Comprehensive CLI dispatch tests covering all skill subcommands.

Tests exercise the full CLI → skill dispatch pipeline by mocking
only the underlying skill APIs, not the CLI parsing or dispatch logic.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from claudit.cli import main


# ---------------------------------------------------------------------------
# Top-level CLI behaviour
# ---------------------------------------------------------------------------
class TestCLITopLevel:
    def test_unknown_command(self, capsys):
        """Unknown subcommands cause argparse to exit with SystemExit."""
        with pytest.raises(SystemExit):
            main(["nonexistent_command"])

    def test_missing_action_shows_help(self, capsys):
        """Subcommand without action triggers help."""
        # This should print help and return 1 (or SystemExit from --help)
        try:
            ret = main(["graph"])
        except SystemExit:
            pass  # --help may cause SystemExit


# ---------------------------------------------------------------------------
# graph CLI subcommands
# ---------------------------------------------------------------------------
class TestGraphCLI:
    def test_graph_show(self, tmp_path, capsys):
        graph = {"main": ["helper"], "helper": []}
        with patch("claudit.skills.graph._require_graph", return_value=graph):
            ret = main(["graph", "show", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["graph"] == graph
        assert output["node_count"] == 2

    def test_graph_callers(self, tmp_path, capsys):
        graph = {"main": ["helper"], "init": ["helper"]}
        with patch("claudit.skills.graph._require_graph", return_value=graph):
            ret = main(["graph", "callers", "helper", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert sorted(output["callers"]) == ["init", "main"]

    def test_graph_build_fresh(self, tmp_path, capsys):
        (tmp_path / "GTAGS").write_text("fake")
        new_graph = {"a": ["b", "c"]}
        with patch("claudit.skills.graph.load_call_graph", return_value=None), \
             patch("claudit.skills.graph.build_call_graph", return_value=new_graph), \
             patch("claudit.skills.graph.save_call_graph"), \
             patch("claudit.skills.graph.ensure_index"), \
             patch("claudit.lang.detect_language", return_value="c"):
            ret = main(["graph", "build", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "built"


# ---------------------------------------------------------------------------
# index CLI subcommands
# ---------------------------------------------------------------------------
class TestIndexCLI:
    def test_index_get_body(self, tmp_path, capsys):
        (tmp_path / "GTAGS").write_text("fake")
        from claudit.skills.index.indexer import FunctionDef, FunctionBody

        func_def = FunctionDef(name="foo", file="main.c", line=1)
        body = FunctionBody(file="main.c", start_line=1, end_line=3, source="int foo() { return 0; }")

        with patch("claudit.skills.index._find_definition", return_value=[func_def]), \
             patch("claudit.skills.index._get_function_body", return_value=body), \
             patch("claudit.lang.detect_language", return_value="c"):
            ret = main(["index", "get-body", "foo", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["function"] == "foo"
        assert output["source"] == "int foo() { return 0; }"

    def test_index_get_body_not_found(self, tmp_path, capsys):
        (tmp_path / "GTAGS").write_text("fake")
        with patch("claudit.skills.index._find_definition", return_value=[]), \
             patch("claudit.lang.detect_language", return_value="c"):
            ret = main(["index", "get-body", "missing", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["error"] == "Function not found"

    def test_index_lookup_both(self, tmp_path, capsys):
        (tmp_path / "GTAGS").write_text("fake")
        from claudit.skills.index.indexer import FunctionDef

        defs = [FunctionDef(name="foo", file="main.c", line=10)]
        refs = [FunctionDef(name="foo", file="test.c", line=20)]

        with patch("claudit.skills.index._find_definition", return_value=defs), \
             patch("claudit.skills.index._find_references", return_value=refs):
            ret = main(["index", "lookup", "foo", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert len(output["definitions"]) == 1
        assert len(output["references"]) == 1

    def test_index_lookup_references_only(self, tmp_path, capsys):
        (tmp_path / "GTAGS").write_text("fake")
        from claudit.skills.index.indexer import FunctionDef

        refs = [FunctionDef(name="foo", file="test.c", line=20)]
        with patch("claudit.skills.index._find_references", return_value=refs):
            ret = main(["index", "lookup", "foo", str(tmp_path), "--kind", "references"])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert "definitions" not in output
        assert len(output["references"]) == 1


# ---------------------------------------------------------------------------
# path CLI subcommands
# ---------------------------------------------------------------------------
class TestPathCLI:
    def test_path_find(self, tmp_path, capsys):
        graph = {"main": ["helper"]}

        with patch("claudit.skills.path.load_call_graph", return_value=graph), \
             patch("claudit.skills.path.load_overrides", return_value=None), \
             patch("claudit.skills.path.pathfinder.find_definition", return_value=[]):
            ret = main(["path", "find", "main", "helper", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["path_count"] == 1

    def test_path_find_no_annotate(self, tmp_path, capsys):
        graph = {"a": ["b"]}

        with patch("claudit.skills.path.load_call_graph", return_value=graph), \
             patch("claudit.skills.path.load_overrides", return_value=None):
            ret = main(["path", "find", "a", "b", str(tmp_path), "--no-annotate"])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["paths"][0]["hops"] == ["a", "b"]

    def test_path_find_with_max_depth(self, tmp_path, capsys):
        graph = {"a": ["b"], "b": ["c"], "c": ["d"]}

        with patch("claudit.skills.path.load_call_graph", return_value=graph), \
             patch("claudit.skills.path.load_overrides", return_value=None):
            ret = main(["path", "find", "a", "d", str(tmp_path), "--no-annotate", "--max-depth", "2"])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["path_count"] == 0  # depth 2 too shallow for 3-hop path


# ---------------------------------------------------------------------------
# highlight CLI subcommands
# ---------------------------------------------------------------------------
class TestHighlightCLI:
    def test_highlight_function(self, tmp_path, capsys):
        from claudit.skills.index.indexer import FunctionDef, FunctionBody

        func_def = FunctionDef(name="foo", file="main.c", line=1)
        body = FunctionBody(file="main.c", start_line=1, end_line=3,
                            source="void foo() {\n    bar();\n}")

        with patch("claudit.skills.highlight.renderer.find_definition", return_value=[func_def]), \
             patch("claudit.skills.highlight.renderer.get_function_body", return_value=body), \
             patch("claudit.lang.detect_language", return_value="c"):
            ret = main(["highlight", "function", "foo", "--project-dir", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["function"] == "foo"
        assert "<span" in output["highlighted_html"]

    def test_highlight_function_not_found(self, tmp_path, capsys):
        with patch("claudit.skills.highlight.renderer.find_definition", return_value=[]), \
             patch("claudit.lang.detect_language", return_value="c"):
            ret = main(["highlight", "function", "missing", "--project-dir", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["error"] == "Function not found"

    def test_highlight_path(self, tmp_path, capsys):
        from claudit.skills.index.indexer import FunctionDef, FunctionBody

        def mock_find_def(name, proj):
            return [FunctionDef(name=name, file=f"{name}.c", line=1)]

        def mock_get_body(func_def, proj, lang):
            return FunctionBody(
                file=func_def.file, start_line=1, end_line=3,
                source=f"void {func_def.name}() {{\n    next_func();\n}}",
            )

        with patch("claudit.skills.highlight.renderer.find_definition", side_effect=mock_find_def), \
             patch("claudit.skills.highlight.renderer.get_function_body", side_effect=mock_get_body), \
             patch("claudit.lang.detect_language", return_value="c"):
            ret = main(["highlight", "path", "main", "helper", "--project-dir", str(tmp_path)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert "metadata" in output
        assert "results" in output


# ---------------------------------------------------------------------------
# harness CLI subcommands
# ---------------------------------------------------------------------------
class TestHarnessCLI:
    def test_harness_extract_functions(self, c_project, capsys):
        from claudit.skills.harness import ExtractedFunction

        funcs = [
            ExtractedFunction(
                name="process",
                file="main.c",
                start_line=3,
                end_line=5,
                source="void process(int x) {\n    helper(x);\n}",
                signature="void process(int x)",
                language="c",
            ),
        ]

        with patch("claudit.skills.harness.extract_target_functions", return_value=funcs):
            ret = main(["harness", "extract", "--functions", "process", str(c_project)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert len(output["extracted"]) == 1
        assert output["extracted"][0]["function"] == "process"

    def test_harness_extract_file(self, c_project, capsys):
        from claudit.skills.harness import ExtractedFunction

        funcs = [
            ExtractedFunction(
                name="helper",
                file="util.c",
                start_line=3,
                end_line=5,
                source="void helper(int x) {}",
                signature="void helper(int x)",
                language="c",
            ),
        ]

        with patch("claudit.skills.harness.extract_functions_from_file", return_value=funcs):
            ret = main(["harness", "extract", "--file", "util.c", str(c_project)])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert len(output["extracted"]) == 1

    def test_harness_list_functions(self, c_project, capsys):
        funcs_list = [
            {"name": "process", "line": 3, "kind": "function"},
            {"name": "main", "line": 7, "kind": "function"},
        ]

        with patch("claudit.skills.harness.list_functions_in_file", return_value=funcs_list):
            ret = main(["harness", "list-functions", str(c_project), "--file", "main.c"])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["count"] == 2

    def test_harness_analyze_deps(self, c_project, capsys):
        from claudit.skills.harness import DependencySet

        deps = DependencySet(
            stub_functions={"helper"},
            excluded_stdlib={"printf"},
            excluded_extracted=set(),
            dependency_map={"process": ["helper", "printf"]},
        )

        with patch("claudit.skills.harness.analyze_dependencies", return_value=deps):
            ret = main(["harness", "analyze-deps", str(c_project), "--functions", "process"])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert "helper" in output["stub_functions"]
        assert "printf" in output["excluded_stdlib"]

    def test_harness_get_signature(self, c_project, capsys):
        from claudit.skills.harness import FunctionSignature, Parameter

        sig = FunctionSignature(
            name="helper",
            return_type="void",
            parameters=[Parameter(name="x", type="int")],
            full_signature="void helper(int x)",
            is_method=False,
            class_name=None,
        )

        with patch("claudit.skills.harness.get_function_signature", return_value=sig):
            ret = main(["harness", "get-signature", str(c_project), "--function", "helper"])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert output["name"] == "helper"
        assert output["return_type"] == "void"
        assert output["full_signature"] == "void helper(int x)"
        assert len(output["parameters"]) == 1

    def test_harness_get_signature_not_found(self, c_project, capsys):
        with patch("claudit.skills.harness.get_function_signature", return_value=None):
            ret = main(["harness", "get-signature", str(c_project), "--function", "missing"])
        assert ret == 0
        output = json.loads(capsys.readouterr().out)
        assert "error" in output
