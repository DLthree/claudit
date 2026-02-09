"""Extract functions verbatim from source files.

This module uses the index skill to extract function bodies exactly as they
appear in the source code, preserving formatting, comments, and whitespace.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from claudit.skills.index import get_body
from claudit.skills.index.indexer import get_ctags_tags
from claudit.skills.harness.signature_extractor import extract_signature


@dataclass
class ExtractedFunction:
    """A function extracted verbatim from source."""

    name: str
    file: str
    start_line: int
    end_line: int
    source: str
    signature: str
    language: str


def extract_target_functions(
    project_dir: str,
    function_names: list[str],
    language: str,
) -> list[ExtractedFunction]:
    """Extract specified functions verbatim using index.get_body.

    Args:
        project_dir: Project directory
        function_names: List of function names to extract
        language: Target language (c, java, python)

    Returns:
        List of ExtractedFunction objects

    Raises:
        ValueError: If a function cannot be found
    """
    extracted = []

    for func_name in function_names:
        # Use index.get_body to extract function source
        body_result = get_body(
            project_dir,
            func_name,
            language=language,
            auto_index=True,
        )

        if body_result is None:
            raise ValueError(f"Function '{func_name}' not found in project")

        # Extract signature
        filepath = Path(project_dir) / body_result["file"]
        sig = extract_signature(str(filepath), func_name, language)

        signature_str = sig.full_signature if sig else f"{func_name}(...)"

        # Create ExtractedFunction object
        extracted.append(
            ExtractedFunction(
                name=func_name,
                file=body_result["file"],
                start_line=body_result["start_line"],
                end_line=body_result["end_line"],
                source=body_result["source"],
                signature=signature_str,
                language=language,
            )
        )

    return extracted


def extract_functions_from_file(
    project_dir: str,
    filepath: str,
    language: str,
) -> list[ExtractedFunction]:
    """Extract all functions defined in a specific file.

    Args:
        project_dir: Project directory
        filepath: Relative path to source file from project root
        language: Target language (c, java, python)

    Returns:
        List of ExtractedFunction objects

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    # Resolve file path
    root = Path(project_dir).resolve()
    full_path = root / filepath

    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Use ctags to list all functions in file
    tags = get_ctags_tags(str(full_path))

    # Filter for function/method definitions
    function_tags = [
        tag
        for tag in tags
        if tag.get("kind") in ("function", "method", "def")
        and tag.get("name")
    ]

    # Extract function names
    function_names = [tag["name"] for tag in function_tags]

    if not function_names:
        # No functions found in file
        return []

    # Extract all functions
    return extract_target_functions(project_dir, function_names, language)


def list_functions_in_file(
    project_dir: str,
    filepath: str,
) -> list[dict]:
    """List all functions in a file without extracting bodies.

    Args:
        project_dir: Project directory
        filepath: Relative path to source file

    Returns:
        List of dicts with keys: name, line, kind
    """
    root = Path(project_dir).resolve()
    full_path = root / filepath

    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    tags = get_ctags_tags(str(full_path))

    functions = []
    for tag in tags:
        if tag.get("kind") in ("function", "method", "def"):
            functions.append(
                {
                    "name": tag.get("name", ""),
                    "line": tag.get("line", 0),
                    "kind": tag.get("kind", ""),
                }
            )

    return functions
