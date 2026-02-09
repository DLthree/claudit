"""Analyze dependencies of extracted functions using call graph.

This module identifies which functions need to be stubbed by analyzing
the call graph and filtering out already-extracted functions and standard
library functions.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class DependencySet:
    """Set of dependencies requiring stubs."""

    stub_functions: set[str] = field(default_factory=set)
    excluded_stdlib: set[str] = field(default_factory=set)
    excluded_extracted: set[str] = field(default_factory=set)
    dependency_map: dict[str, list[str]] = field(default_factory=dict)


def analyze_dependencies(
    project_dir: str,
    extracted_function_names: set[str],
    call_graph: dict[str, list[str]],
    stub_depth: int = 1,
) -> DependencySet:
    """Identify all dependencies that need stubbing.

    Args:
        project_dir: Project directory
        extracted_function_names: Set of function names already extracted
        call_graph: Call graph mapping function -> callees
        stub_depth: How many levels deep to analyze dependencies

    Returns:
        DependencySet with functions to stub and exclusions
    """
    result = DependencySet()

    # Track all functions we've seen in the call graph (project functions)
    project_functions = set(call_graph.keys())

    # BFS to find dependencies up to stub_depth
    queue: deque[tuple[str, int]] = deque()

    # Start with extracted functions at depth 0
    for func in extracted_function_names:
        queue.append((func, 0))

    visited = set(extracted_function_names)

    while queue:
        func, depth = queue.popleft()

        # Stop if we've reached max depth
        if depth >= stub_depth:
            continue

        # Get direct callees
        callees = call_graph.get(func, [])

        # Record dependency relationship
        if callees:
            result.dependency_map[func] = callees

        for callee in callees:
            if callee in visited:
                continue

            visited.add(callee)

            # Categorize the callee
            if callee in extracted_function_names:
                # Already extracted - no need to stub
                result.excluded_extracted.add(callee)
            elif callee not in project_functions:
                # Not in call graph - likely stdlib
                result.excluded_stdlib.add(callee)
            elif _is_stdlib_function(callee):
                # Known stdlib function
                result.excluded_stdlib.add(callee)
            else:
                # Project function that needs stubbing
                result.stub_functions.add(callee)

                # Continue BFS from this function
                queue.append((callee, depth + 1))

    return result


def _is_stdlib_function(func_name: str) -> bool:
    """Heuristic: check if function is likely a standard library function.

    This is a best-effort heuristic and may have false positives/negatives.
    """
    # C standard library functions (common ones)
    c_stdlib = {
        # stdio.h
        "printf",
        "fprintf",
        "sprintf",
        "snprintf",
        "scanf",
        "fscanf",
        "sscanf",
        "fopen",
        "fclose",
        "fread",
        "fwrite",
        "fgets",
        "fputs",
        "getc",
        "putc",
        "feof",
        "ferror",
        "fflush",
        "fseek",
        "ftell",
        "rewind",
        "perror",
        # stdlib.h
        "malloc",
        "calloc",
        "realloc",
        "free",
        "exit",
        "abort",
        "atexit",
        "atoi",
        "atof",
        "atol",
        "strtol",
        "strtod",
        "rand",
        "srand",
        "qsort",
        "bsearch",
        # string.h
        "strlen",
        "strcpy",
        "strncpy",
        "strcat",
        "strncat",
        "strcmp",
        "strncmp",
        "strchr",
        "strrchr",
        "strstr",
        "strtok",
        "memcpy",
        "memmove",
        "memset",
        "memcmp",
        # math.h
        "sin",
        "cos",
        "tan",
        "sqrt",
        "pow",
        "exp",
        "log",
        "floor",
        "ceil",
        # time.h
        "time",
        "clock",
        "difftime",
        "mktime",
        # unistd.h / POSIX
        "read",
        "write",
        "open",
        "close",
        "lseek",
        "getpid",
        "fork",
        "exec",
        "execve",
        # ctype.h
        "isalpha",
        "isdigit",
        "isalnum",
        "isspace",
        "toupper",
        "tolower",
    }

    # Java standard library patterns (common packages)
    java_stdlib_prefixes = [
        "System.",
        "String.",
        "Integer.",
        "Long.",
        "Double.",
        "Math.",
        "Thread.",
        "Object.",
        "Class.",
        "Exception.",
    ]

    # Python built-ins (common ones)
    python_builtins = {
        "print",
        "len",
        "range",
        "enumerate",
        "zip",
        "map",
        "filter",
        "sum",
        "min",
        "max",
        "sorted",
        "list",
        "dict",
        "set",
        "tuple",
        "str",
        "int",
        "float",
        "bool",
        "open",
        "isinstance",
        "hasattr",
        "getattr",
        "setattr",
    }

    # Check C stdlib
    if func_name in c_stdlib:
        return True

    # Check Java stdlib patterns
    for prefix in java_stdlib_prefixes:
        if func_name.startswith(prefix):
            return True

    # Check Python builtins
    if func_name in python_builtins:
        return True

    return False


def filter_stub_functions(
    stub_functions: set[str],
    project_dir: str,
) -> set[str]:
    """Filter out functions that can't be found in the project.

    This removes functions that are likely external dependencies or
    truly stdlib functions that weren't caught by the heuristic.

    Args:
        stub_functions: Initial set of functions to stub
        project_dir: Project directory

    Returns:
        Filtered set of functions that exist in the project
    """
    from claudit.skills.index import lookup

    filtered = set()

    for func in stub_functions:
        try:
            # Try to look up the function
            result = lookup(project_dir, func, kind="definitions", auto_index=False)

            # If we found a definition, keep it
            if result.get("definitions"):
                filtered.add(func)
        except Exception:
            # If lookup fails, exclude it (likely stdlib or external)
            pass

    return filtered
