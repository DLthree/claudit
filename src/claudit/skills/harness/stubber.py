"""Generate stub implementations for dependency functions.

This module creates minimal stub implementations that return appropriate
default values, allowing extracted functions to compile/run independently.
"""

from __future__ import annotations

from dataclasses import dataclass

from claudit.skills.harness.signature_extractor import (
    FunctionSignature,
    extract_signature,
)


@dataclass
class StubFunction:
    """A stubbed dependency function."""

    name: str
    signature: str
    stub_source: str
    return_type: str
    reason: str
    original_file: str | None = None


def generate_stubs(
    project_dir: str,
    stub_functions: set[str],
    language: str,
    dependency_map: dict[str, list[str]],
) -> list[StubFunction]:
    """Generate stub implementations for all dependency functions.

    Args:
        project_dir: Project directory
        stub_functions: Set of function names to stub
        language: Target language (c, java, python)
        dependency_map: Map of caller -> callees for context

    Returns:
        List of StubFunction objects
    """
    stubs = []

    # Build reverse map: callee -> callers
    reverse_map: dict[str, list[str]] = {}
    for caller, callees in dependency_map.items():
        for callee in callees:
            reverse_map.setdefault(callee, []).append(caller)

    for func_name in sorted(stub_functions):
        # Determine reason for stubbing
        callers = reverse_map.get(func_name, [])
        reason = f"called_by {', '.join(callers[:3])}" if callers else "dependency"

        # Try to extract signature (may fail if function is from stdlib)
        sig = _find_signature(project_dir, func_name, language)

        if sig is None:
            # Create minimal stub without signature info
            stub = _create_minimal_stub(func_name, language)
        else:
            # Generate language-specific stub
            if language == "c":
                stub_source = _generate_c_stub(sig)
            elif language == "java":
                stub_source = _generate_java_stub(sig)
            elif language == "python":
                stub_source = _generate_python_stub(sig)
            else:
                stub_source = _generate_generic_stub(sig)

            stub = StubFunction(
                name=func_name,
                signature=sig.full_signature,
                stub_source=stub_source,
                return_type=sig.return_type,
                reason=reason,
            )

        stubs.append(stub)

    return stubs


def _find_signature(
    project_dir: str, func_name: str, language: str
) -> FunctionSignature | None:
    """Try to find function signature in project."""
    from pathlib import Path
    from claudit.skills.index import lookup

    try:
        # Look up function definition
        result = lookup(project_dir, func_name, kind="definitions", auto_index=True)

        if result.get("definitions"):
            # Get first definition
            defn = result["definitions"][0]
            filepath = Path(project_dir) / defn["file"]

            # Extract signature
            return extract_signature(str(filepath), func_name, language)

    except Exception:
        pass

    return None


def _create_minimal_stub(func_name: str, language: str) -> StubFunction:
    """Create minimal stub when signature is unknown."""
    if language == "c":
        stub_source = f"void {func_name}(void) {{\n    /* AUTO-GENERATED STUB - UNKNOWN SIGNATURE */\n}}"
        return StubFunction(
            name=func_name,
            signature=f"void {func_name}(void)",
            stub_source=stub_source,
            return_type="void",
            reason="unknown_signature",
        )
    elif language == "java":
        stub_source = f"void {func_name}() {{\n    /* AUTO-GENERATED STUB - UNKNOWN SIGNATURE */\n}}"
        return StubFunction(
            name=func_name,
            signature=f"void {func_name}()",
            stub_source=stub_source,
            return_type="void",
            reason="unknown_signature",
        )
    else:  # python
        stub_source = f"def {func_name}():\n    \"\"\"AUTO-GENERATED STUB - UNKNOWN SIGNATURE\"\"\"\n    pass"
        return StubFunction(
            name=func_name,
            signature=f"def {func_name}()",
            stub_source=stub_source,
            return_type="",
            reason="unknown_signature",
        )


def _generate_c_stub(sig: FunctionSignature) -> str:
    """Generate C stub implementation."""
    # Get default return value
    default_return = _infer_c_default_return(sig.return_type)

    # Build parameter list
    if sig.parameters:
        params = ", ".join(
            f"{p.type} {p.name}".strip() if p.type else p.name
            for p in sig.parameters
        )
    else:
        params = "void"

    # Build function
    lines = [f"{sig.return_type} {sig.name}({params}) {{"]
    lines.append("    /* AUTO-GENERATED STUB */")

    if default_return:
        lines.append(f"    return {default_return};")

    lines.append("}")

    return "\n".join(lines)


def _generate_java_stub(sig: FunctionSignature) -> str:
    """Generate Java stub implementation."""
    # Get default return value
    default_return = _infer_java_default_return(sig.return_type)

    # Build parameter list
    params = ", ".join(f"{p.type} {p.name}".strip() for p in sig.parameters)

    # Build method
    access = "public static" if sig.is_static else "public"
    lines = [f"{access} {sig.return_type} {sig.name}({params}) {{"]
    lines.append("    /* AUTO-GENERATED STUB */")

    if default_return:
        lines.append(f"    return {default_return};")

    lines.append("}")

    return "\n".join(lines)


def _generate_python_stub(sig: FunctionSignature) -> str:
    """Generate Python stub implementation."""
    # Build parameter list
    params = ", ".join(p.name for p in sig.parameters)

    # Build function
    lines = [f"def {sig.name}({params}):"]
    lines.append('    """AUTO-GENERATED STUB"""')

    if sig.return_type and sig.return_type not in ("None", ""):
        lines.append("    return None")
    else:
        lines.append("    pass")

    return "\n".join(lines)


def _generate_generic_stub(sig: FunctionSignature) -> str:
    """Generate generic stub (fallback)."""
    return f"{sig.full_signature} {{\n    /* AUTO-GENERATED STUB */\n}}"


def _infer_c_default_return(return_type: str) -> str | None:
    """Infer appropriate default return value for C type."""
    if not return_type or return_type.strip() == "void":
        return None

    rtype = return_type.strip().lower()

    # Pointer types
    if "*" in return_type:
        return "NULL"

    # Integer types
    if any(
        t in rtype
        for t in ["int", "long", "short", "char", "size_t", "ssize_t", "off_t"]
    ):
        return "0"

    # Floating point
    if any(t in rtype for t in ["float", "double"]):
        return "0.0"

    # Boolean (C99+)
    if "bool" in rtype or "_Bool" in rtype:
        return "false"

    # Struct (usually returned by value is complex, return zeroed)
    if "struct" in rtype:
        # Extract struct name and return zeroed initializer
        # Example: "struct foo" -> "(struct foo){0}"
        return f"({return_type}){{0}}"

    # Default: try returning 0
    return "0"


def _infer_java_default_return(return_type: str) -> str | None:
    """Infer appropriate default return value for Java type."""
    if not return_type or return_type.strip() == "void":
        return None

    rtype = return_type.strip()

    # Primitive types
    primitives = {
        "int": "0",
        "long": "0L",
        "short": "(short)0",
        "byte": "(byte)0",
        "char": "'\\0'",
        "float": "0.0f",
        "double": "0.0",
        "boolean": "false",
    }

    if rtype in primitives:
        return primitives[rtype]

    # Object types (including String, arrays, etc.)
    return "null"


def _infer_python_default_return(return_type: str) -> str:
    """Infer appropriate default return value for Python."""
    # Python always returns None by default
    return "None"
