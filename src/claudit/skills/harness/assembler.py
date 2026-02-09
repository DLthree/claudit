"""Assemble complete test harness from extracted functions and stubs.

This module combines extracted functions, stub implementations, includes,
and optional main() function into a complete, runnable test harness.
"""

from __future__ import annotations

import re
from pathlib import Path

from claudit.skills.harness.extractor import ExtractedFunction
from claudit.skills.harness.stubber import StubFunction


def assemble_harness(
    project_dir: str,
    extracted: list[ExtractedFunction],
    stubs: list[StubFunction],
    language: str,
    include_main: bool = False,
) -> str:
    """Combine extracted functions and stubs into complete harness.

    Args:
        project_dir: Project directory
        extracted: List of extracted functions
        stubs: List of stub functions
        language: Target language (c, java, python)
        include_main: Whether to generate a main() function

    Returns:
        Complete harness source code as string
    """
    sections = []

    # Header comment
    sections.append(_generate_header_comment(language, len(extracted), len(stubs)))

    # Includes/imports
    includes = extract_includes(project_dir, extracted, language)
    if includes:
        sections.append("\n".join(includes))

    # Language-specific assembly
    if language == "c":
        harness = _assemble_c_harness(
            sections, extracted, stubs, includes, include_main
        )
    elif language == "java":
        harness = _assemble_java_harness(
            sections, extracted, stubs, includes, include_main
        )
    elif language == "python":
        harness = _assemble_python_harness(
            sections, extracted, stubs, includes, include_main
        )
    else:
        harness = _assemble_generic_harness(sections, extracted, stubs, include_main)

    return harness


def extract_includes(
    project_dir: str,
    extracted: list[ExtractedFunction],
    language: str,
) -> list[str]:
    """Extract #include or import statements from original files.

    Args:
        project_dir: Project directory
        extracted: List of extracted functions
        language: Target language

    Returns:
        List of include/import statements
    """
    includes_set = set()
    root = Path(project_dir).resolve()

    for func in extracted:
        filepath = root / func.file

        try:
            content = filepath.read_text(errors="replace")
            file_includes = _extract_includes_from_content(content, language)
            includes_set.update(file_includes)
        except Exception:
            continue

    # Return sorted for deterministic output
    return sorted(includes_set)


def _extract_includes_from_content(content: str, language: str) -> set[str]:
    """Extract include/import statements from file content."""
    includes = set()

    if language == "c":
        # Match #include <...> and #include "..."
        for match in re.finditer(r'^\s*#include\s+[<"][^>"]+[>"]', content, re.MULTILINE):
            includes.add(match.group(0).strip())

    elif language == "java":
        # Match import statements
        for match in re.finditer(r'^\s*import\s+[\w.]+\s*;', content, re.MULTILINE):
            includes.add(match.group(0).strip())

    elif language == "python":
        # Match import and from...import statements
        for match in re.finditer(
            r'^\s*(import\s+[\w.]+|from\s+[\w.]+\s+import\s+.+)', content, re.MULTILINE
        ):
            includes.add(match.group(0).strip())

    return includes


def _generate_header_comment(language: str, extracted_count: int, stub_count: int) -> str:
    """Generate header comment for harness."""
    if language == "python":
        return f'''"""AUTO-GENERATED TEST HARNESS
Extracted functions: {extracted_count}
Stub functions: {stub_count}
"""'''
    elif language == "java":
        return f'''/**
 * AUTO-GENERATED TEST HARNESS
 * Extracted functions: {extracted_count}
 * Stub functions: {stub_count}
 */'''
    else:  # C and generic
        return f'''/*
 * AUTO-GENERATED TEST HARNESS
 * Extracted functions: {extracted_count}
 * Stub functions: {stub_count}
 */'''


def _assemble_c_harness(
    sections: list[str],
    extracted: list[ExtractedFunction],
    stubs: list[StubFunction],
    includes: list[str],
    include_main: bool,
) -> str:
    """Assemble C harness."""
    # Add forward declarations for stubs
    if stubs:
        sections.append("\n/* Forward declarations for stubs */")
        for stub in stubs:
            # Extract just the signature (before {)
            sig = stub.signature.split("{")[0].strip()
            sections.append(f"{sig};")

    # Add stub implementations
    if stubs:
        sections.append("\n/* Stub implementations */")
        for stub in stubs:
            sections.append(f"\n{stub.stub_source}")

    # Add extracted functions (verbatim!)
    if extracted:
        sections.append("\n/* Extracted functions */")
        for func in extracted:
            sections.append(f"\n{func.source}")

    # Optional main function
    if include_main:
        main_func = _generate_c_main(extracted)
        sections.append(f"\n/* Test main */\n{main_func}")

    return "\n".join(sections) + "\n"


def _assemble_java_harness(
    sections: list[str],
    extracted: list[ExtractedFunction],
    stubs: list[StubFunction],
    includes: list[str],
    include_main: bool,
) -> str:
    """Assemble Java harness."""
    # Java needs a class wrapper
    sections.append("\npublic class TestHarness {")

    # Add stub methods
    if stubs:
        sections.append("    /* Stub implementations */")
        for stub in stubs:
            # Indent stub source
            indented = "\n".join("    " + line for line in stub.stub_source.split("\n"))
            sections.append(f"\n{indented}")

    # Add extracted methods
    if extracted:
        sections.append("    /* Extracted methods */")
        for func in extracted:
            # Indent function source
            indented = "\n".join("    " + line for line in func.source.split("\n"))
            sections.append(f"\n{indented}")

    # Optional main method
    if include_main:
        main_func = _generate_java_main(extracted)
        sections.append(f"\n    /* Test main */\n{main_func}")

    sections.append("}")

    return "\n".join(sections) + "\n"


def _assemble_python_harness(
    sections: list[str],
    extracted: list[ExtractedFunction],
    stubs: list[StubFunction],
    includes: list[str],
    include_main: bool,
) -> str:
    """Assemble Python harness."""
    # Add stub functions
    if stubs:
        sections.append("# Stub implementations")
        for stub in stubs:
            sections.append(f"\n{stub.stub_source}")

    # Add extracted functions (verbatim!)
    if extracted:
        sections.append("\n# Extracted functions")
        for func in extracted:
            sections.append(f"\n{func.source}")

    # Optional main block
    if include_main:
        main_func = _generate_python_main(extracted)
        sections.append(f"\n# Test main\n{main_func}")

    return "\n".join(sections) + "\n"


def _assemble_generic_harness(
    sections: list[str],
    extracted: list[ExtractedFunction],
    stubs: list[StubFunction],
    include_main: bool,
) -> str:
    """Assemble generic harness (fallback)."""
    # Just concatenate stubs and extracted functions
    if stubs:
        sections.append("\n/* Stub implementations */")
        for stub in stubs:
            sections.append(f"\n{stub.stub_source}")

    if extracted:
        sections.append("\n/* Extracted functions */")
        for func in extracted:
            sections.append(f"\n{func.source}")

    return "\n".join(sections) + "\n"


def _generate_c_main(extracted: list[ExtractedFunction]) -> str:
    """Generate minimal main() function for C."""
    lines = ["int main(void) {"]
    lines.append("    /* TODO: Add test calls here */")

    for func in extracted[:3]:  # Show first 3 as examples
        lines.append(f"    /* Example: {func.name}(...); */")

    lines.append("    return 0;")
    lines.append("}")

    return "\n".join(lines)


def _generate_java_main(extracted: list[ExtractedFunction]) -> str:
    """Generate minimal main() method for Java."""
    lines = ["    public static void main(String[] args) {"]
    lines.append("        /* TODO: Add test calls here */")

    for func in extracted[:3]:
        lines.append(f"        /* Example: {func.name}(...); */")

    lines.append("    }")

    return "\n".join(lines)


def _generate_python_main(extracted: list[ExtractedFunction]) -> str:
    """Generate minimal main block for Python."""
    lines = ['if __name__ == "__main__":']
    lines.append("    # TODO: Add test calls here")

    for func in extracted[:3]:
        lines.append(f"    # Example: {func.name}(...)")

    return "\n".join(lines)
