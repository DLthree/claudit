---
name: harness
description: Create standalone test harnesses through iterative, LLM-guided extraction and compilation. Use when the user asks to create a harness for a function, extract code for standalone testing, create an isolated test environment, pull out code for fuzzing, or stub dependencies for unit testing.
compatibility: Requires GNU Global and Universal Ctags
---

## Concept

The harness skill helps create isolated test environments for specific functions by:
1. **Extracting** target code verbatim from a larger codebase
2. **Analyzing** dependencies to understand what's missing
3. **Iteratively compiling** and fixing errors until you have a working harness

**Key principle**: The LLM makes decisions about what to extract, what to stub, and how to fix compilation errors based on the specific use case and error messages.

## Iterative Workflow

### 1. Create Skeleton Project

Create a minimal project structure appropriate for the language (Makefile/CMakeLists for C, pom.xml for Java, requirements.txt for Python).

### 2. Extract Target Code

Use the extraction utilities to pull over specific functions or entire files:

```bash
claudit harness extract /path/to/project --functions authenticate_user,validate_token
claudit harness extract /path/to/project --file src/auth/security.c
claudit harness list-functions /path/to/project --file src/auth/security.c
```

Copy the extracted source into your harness project files.

### 3. Attempt Compilation

Try to build/run the harness. Analyze errors to understand what's missing.

### 4. Diagnose and Fix

**Common error patterns:**
- **Undefined reference**: Missing function -- need to stub or extract
- **Undeclared identifier**: Missing type/struct definition -- extract or define
- **Missing header**: Need to add includes or copy definitions
- **Wrong signature**: Need to adjust stub signature

**Use dependency analysis to help:**
```bash
claudit harness analyze-deps /path/to/project --functions authenticate_user --depth 2
```

### 5. Stub vs Extract Decision

**Stub when**: function is simple utility (logging, metrics), has complex dependencies you don't need, is I/O or external service, or you want to control the return value.

**Extract when**: function contains critical business logic, is tightly coupled to target code, or you need the real implementation.

### 6. Repeat Until Working

Continue: compile, read errors, stub or extract, compile again.

For a full worked example, see [references/workflow-example.md](references/workflow-example.md).

## CLI Commands

**Invocation:** Use the `claudit` CLI only. Do not run `python -m claudit.skills.harness`.

```bash
claudit harness extract <project_dir> --functions func1,func2 [--language c|java|python]
claudit harness extract <project_dir> --file path/to/file.c [--language c|java|python]
claudit harness list-functions <project_dir> --file path/to/file.c
claudit harness analyze-deps <project_dir> --functions func1,func2 [--depth 2]
claudit harness get-signature <project_dir> --function func_name [--language c]
```

## Python API

```python
from claudit.skills.harness import (
    extract_function,
    extract_functions,
    extract_file,
    list_functions_in_file,
    analyze_dependencies,
    get_function_signature,
    get_function_callees,
)

# Extract single function
func = extract_function("/path/to/project", "authenticate_user", language="c")
# Returns: ExtractedFunction(name, file, start_line, end_line, source, signature)

# Extract multiple functions
funcs = extract_functions("/path/to/project", ["func1", "func2"], language="c")

# Extract all functions from a file
funcs = extract_file("/path/to/project", "src/auth/security.c", language="c")

# List functions (discovery)
functions = list_functions_in_file("/path/to/project", "src/auth/security.c")
# Returns: [{"name": "func1", "line": 42, "kind": "function"}, ...]

# Analyze dependencies
deps = analyze_dependencies("/path/to/project", ["authenticate_user"], depth=2)
# Returns: DependencySet(stub_functions, dependency_map, excluded_stdlib)

# Get function signature for stubbing
sig = get_function_signature("/path/to/project", "validate_credentials", language="c")
# Returns: FunctionSignature(name, return_type, parameters, full_signature)

# Get direct callees
callees = get_function_callees("/path/to/project", "authenticate_user")
# Returns: ["validate_credentials", "log_event", "check_session"]
```
