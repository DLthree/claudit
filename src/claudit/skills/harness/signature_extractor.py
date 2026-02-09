"""Extract function signatures using Universal Ctags.

This module extracts complete function signatures including return types,
parameter lists, and other metadata needed for stub generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from claudit.skills.index.indexer import get_ctags_tags


@dataclass
class Parameter:
    """Function parameter information."""

    name: str
    type: str = ""  # May be empty for Python


@dataclass
class FunctionSignature:
    """Complete function signature information."""

    name: str
    return_type: str
    parameters: list[Parameter]
    full_signature: str
    is_method: bool = False
    class_name: str | None = None
    is_static: bool = False


def extract_signature(
    filepath: str, function_name: str, language: str
) -> FunctionSignature | None:
    """Extract full function signature from source file.

    Args:
        filepath: Path to source file
        function_name: Name of function to extract
        language: Language hint (c, java, python)

    Returns:
        FunctionSignature if found, None otherwise
    """
    tags = get_ctags_tags(filepath)

    # Find the function tag
    func_tag = None
    for tag in tags:
        if tag.get("name") == function_name and tag.get("kind") in (
            "function",
            "method",
            "def",
        ):
            func_tag = tag
            break

    if func_tag is None:
        return None

    # Parse language-specific signature
    if language == "c":
        return _parse_c_signature(func_tag, filepath)
    elif language == "java":
        return _parse_java_signature(func_tag, filepath)
    elif language == "python":
        return _parse_python_signature(func_tag, filepath)
    else:
        # Fallback: best effort
        return _parse_generic_signature(func_tag, filepath)


def _parse_c_signature(tag: dict, filepath: str) -> FunctionSignature:
    """Parse C function signature from ctags tag."""
    name = tag.get("name", "")
    signature_str = tag.get("signature", "()")

    # Extract return type from typeref or by parsing source
    return_type = "void"
    if "typeref" in tag:
        # Format: "typename:int" or similar
        typeref = tag["typeref"]
        if ":" in typeref:
            return_type = typeref.split(":", 1)[1].strip()
    else:
        # Try to extract from source line
        return_type = _extract_c_return_type(filepath, tag.get("line", 0), name)

    # Parse parameters from signature
    parameters = _parse_c_parameters(signature_str)

    # Build full signature
    param_list = ", ".join(
        f"{p.type} {p.name}".strip() if p.type else p.name for p in parameters
    )
    full_signature = f"{return_type} {name}({param_list})"

    return FunctionSignature(
        name=name,
        return_type=return_type,
        parameters=parameters,
        full_signature=full_signature,
        is_method=False,
    )


def _parse_java_signature(tag: dict, filepath: str) -> FunctionSignature:
    """Parse Java method signature from ctags tag."""
    name = tag.get("name", "")
    signature_str = tag.get("signature", "()")

    # Extract return type
    return_type = "void"
    if "typeref" in tag:
        typeref = tag["typeref"]
        if ":" in typeref:
            return_type = typeref.split(":", 1)[1].strip()

    # Check if this is a method (has class scope)
    is_method = "class" in tag or "scope" in tag
    class_name = tag.get("class") or (
        tag.get("scope", "").split(".")[-1] if "scope" in tag else None
    )

    # Check if static
    is_static = "static" in tag.get("access", "")

    # Parse parameters
    parameters = _parse_java_parameters(signature_str)

    # Build full signature
    param_list = ", ".join(f"{p.type} {p.name}".strip() for p in parameters)
    full_signature = f"{return_type} {name}({param_list})"

    return FunctionSignature(
        name=name,
        return_type=return_type,
        parameters=parameters,
        full_signature=full_signature,
        is_method=is_method,
        class_name=class_name,
        is_static=is_static,
    )


def _parse_python_signature(tag: dict, filepath: str) -> FunctionSignature:
    """Parse Python function signature from ctags tag."""
    name = tag.get("name", "")
    signature_str = tag.get("signature", "()")

    # Python has limited type information in ctags
    # Return type is usually unknown unless we parse type hints
    return_type = ""

    # Check if this is a method
    is_method = "class" in tag or "scope" in tag
    class_name = tag.get("class") or (
        tag.get("scope", "").split(".")[-1] if "scope" in tag else None
    )

    # Parse parameters (names only, types usually unavailable)
    parameters = _parse_python_parameters(signature_str)

    # Build full signature
    param_list = ", ".join(p.name for p in parameters)
    full_signature = f"def {name}({param_list})"

    return FunctionSignature(
        name=name,
        return_type=return_type,
        parameters=parameters,
        full_signature=full_signature,
        is_method=is_method,
        class_name=class_name,
    )


def _parse_generic_signature(tag: dict, filepath: str) -> FunctionSignature:
    """Parse signature with minimal assumptions."""
    name = tag.get("name", "")
    signature_str = tag.get("signature", "()")

    return FunctionSignature(
        name=name,
        return_type="",
        parameters=[],
        full_signature=f"{name}{signature_str}",
        is_method=False,
    )


def _parse_c_parameters(signature_str: str) -> list[Parameter]:
    """Parse C function parameters from signature string."""
    # Signature format: "(type1 name1, type2 name2, ...)"
    params = []

    # Strip parentheses
    sig = signature_str.strip()
    if sig.startswith("(") and sig.endswith(")"):
        sig = sig[1:-1]

    if not sig or sig.strip() in ("void", ""):
        return []

    # Split by comma (simple parser, doesn't handle nested parens)
    parts = [p.strip() for p in sig.split(",")]

    for part in parts:
        if not part:
            continue

        # Split into type and name
        tokens = part.split()
        if len(tokens) >= 2:
            # Last token is name, rest is type
            param_name = tokens[-1].lstrip("*")  # Remove pointer prefix
            param_type = " ".join(tokens[:-1])
            params.append(Parameter(name=param_name, type=param_type))
        elif len(tokens) == 1:
            # Just type or just name
            params.append(Parameter(name=tokens[0], type=""))
        else:
            # Empty or malformed
            params.append(Parameter(name=part, type=""))

    return params


def _parse_java_parameters(signature_str: str) -> list[Parameter]:
    """Parse Java method parameters from signature string."""
    # Similar to C but different syntax
    params = []

    sig = signature_str.strip()
    if sig.startswith("(") and sig.endswith(")"):
        sig = sig[1:-1]

    if not sig:
        return []

    parts = [p.strip() for p in sig.split(",")]

    for part in parts:
        if not part:
            continue

        tokens = part.split()
        if len(tokens) >= 2:
            param_type = " ".join(tokens[:-1])
            param_name = tokens[-1]
            params.append(Parameter(name=param_name, type=param_type))
        else:
            params.append(Parameter(name=part, type=""))

    return params


def _parse_python_parameters(signature_str: str) -> list[Parameter]:
    """Parse Python function parameters from signature string."""
    # Python signature: (arg1, arg2=default, *args, **kwargs)
    params = []

    sig = signature_str.strip()
    if sig.startswith("(") and sig.endswith(")"):
        sig = sig[1:-1]

    if not sig:
        return []

    # Simple split by comma
    parts = [p.strip() for p in sig.split(",")]

    for part in parts:
        if not part:
            continue

        # Remove default values
        param_name = part.split("=")[0].strip()

        # Remove type annotations if present (name: type)
        if ":" in param_name:
            param_name = param_name.split(":")[0].strip()

        params.append(Parameter(name=param_name, type=""))

    return params


def _extract_c_return_type(filepath: str, line_num: int, func_name: str) -> str:
    """Try to extract C return type by parsing the source line."""
    try:
        path = Path(filepath)
        lines = path.read_text(errors="replace").splitlines()

        if line_num <= 0 or line_num > len(lines):
            return "void"

        # Get the function declaration line
        decl_line = lines[line_num - 1].strip()

        # Simple heuristic: return type is before function name
        # Example: "int foo()" -> "int"
        # Example: "static void * bar()" -> "void *"

        if func_name in decl_line:
            before_name = decl_line.split(func_name)[0].strip()

            # Remove storage class specifiers
            for keyword in ["static", "extern", "inline", "__inline__"]:
                before_name = before_name.replace(keyword, "").strip()

            # What remains should be the return type
            if before_name:
                return before_name

    except Exception:
        pass

    return "void"
