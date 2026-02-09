# Test Harness Generation

Create standalone test harnesses through iterative, LLM-guided extraction and compilation.

## Concept

The harness skill helps you create isolated test environments for specific functions by:
1. **Extracting** target code verbatim from a larger codebase
2. **Analyzing** dependencies to understand what's missing
3. **Iteratively compiling** and fixing errors until you have a working harness

**Key principle**: The LLM makes decisions about what to extract, what to stub, and how to fix compilation errors based on the specific use case and error messages.

## When to use

Use this skill when the user asks to:
- "Create a harness for function X"
- "Extract this code and make it standalone"
- "Create a test environment for the authentication logic"
- "Pull out the Spring filter chain into a standalone project"
- "Create an isolated version of this security function for testing"

## Iterative Workflow

### 1. Create Skeleton Project

Start by creating a minimal project structure appropriate for the language:

**C/C++ example:**
```bash
mkdir harness-auth/
cd harness-auth/
# Create minimal CMakeLists.txt or Makefile
# Create main.c with includes
```

**Java/Spring example:**
```bash
mkdir harness-filter/
cd harness-filter/
# Create Maven/Gradle project
# Create minimal pom.xml or build.gradle
# Add necessary dependencies
```

**Python example:**
```bash
mkdir harness-validator/
cd harness-validator/
# Create requirements.txt
# Create __init__.py
```

### 2. Extract Target Code

Use the extraction utilities to pull over specific functions or entire files:

```bash
# Extract specific functions
claudit harness extract /path/to/project --functions authenticate_user,validate_token

# Extract entire file
claudit harness extract /path/to/project --file src/auth/security.c

# List available functions first
claudit harness list-functions /path/to/project --file src/auth/security.c
```

Copy the extracted source into your harness project files.

### 3. Attempt Compilation

Try to build/run the harness:

```bash
# C
gcc -o harness main.c -Wall -Werror

# Java
mvn compile

# Python
python harness.py
```

### 4. Diagnose Compilation Errors

Analyze the errors to understand what's missing:

**Common error patterns:**
- **Undefined reference**: Missing function - need to stub or extract
- **Undeclared identifier**: Missing type/struct definition - extract or define
- **Missing header**: Need to add includes or copy definitions
- **Wrong signature**: Need to adjust stub signature

**Use dependency analysis to help:**
```bash
claudit harness analyze-deps /path/to/project --functions authenticate_user --depth 2
```

This shows you:
- Direct dependencies (functions called by your target)
- Transitive dependencies (up to specified depth)
- Which functions are in the project vs stdlib

### 5. Fix Errors (Stub vs Extract Decision)

The LLM decides based on error context:

**When to STUB:**
- Function is simple utility (logging, metrics)
- Function has complex dependencies you don't need
- Function is I/O or external service call
- You want to control the return value for testing

**Example stub (C):**
```c
// Compilation error: undefined reference to `log_event`
// Decision: Stub it - logging not needed for auth testing

void log_event(const char *event, int severity) {
    // AUTO-GENERATED STUB - no-op for testing
}
```

**When to EXTRACT:**
- Function contains critical business logic
- Function is called multiple times
- Function is tightly coupled to target code
- You need the real implementation for testing

**Example extraction:**
```bash
# Compilation error: undefined reference to `check_password_strength`
# Decision: Extract it - password validation is critical for auth testing

claudit harness extract /path/to/project --functions check_password_strength
# Copy the extracted source into harness
```

### 6. Repeat Until Working

Continue the cycle:
1. Compile
2. Read errors
3. Stub or extract based on LLM analysis
4. Compile again

Each iteration gets you closer to a working harness.

## CLI Commands

```bash
# Extract specific functions
claudit harness extract <project_dir> --functions func1,func2 [--language c|java|python]

# Extract all functions from file
claudit harness extract <project_dir> --file path/to/file.c [--language c|java|python]

# List functions in file (discovery)
claudit harness list-functions <project_dir> --file path/to/file.c

# Analyze dependencies
claudit harness analyze-deps <project_dir> --functions func1,func2 [--depth 2]

# Get function signature
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
func = extract_function(
    project_dir="/path/to/project",
    function_name="authenticate_user",
    language="c"  # auto-detected if omitted
)
# Returns: ExtractedFunction(name, file, start_line, end_line, source, signature)

# Extract multiple functions
funcs = extract_functions(
    project_dir="/path/to/project",
    function_names=["func1", "func2"],
    language="c"
)

# Extract all functions from a file
funcs = extract_file(
    project_dir="/path/to/project",
    filepath="src/auth/security.c",
    language="c"
)

# List functions (discovery)
functions = list_functions_in_file(
    project_dir="/path/to/project",
    filepath="src/auth/security.c"
)
# Returns: [{"name": "func1", "line": 42, "kind": "function"}, ...]

# Analyze dependencies
deps = analyze_dependencies(
    project_dir="/path/to/project",
    function_names=["authenticate_user"],
    depth=2
)
# Returns: DependencySet(stub_functions, dependency_map, excluded_stdlib)

# Get function signature for stubbing
sig = get_function_signature(
    project_dir="/path/to/project",
    function_name="validate_credentials",
    language="c"
)
# Returns: FunctionSignature(name, return_type, parameters, full_signature)

# Get direct callees
callees = get_function_callees(
    project_dir="/path/to/project",
    function_name="authenticate_user"
)
# Returns: ["validate_credentials", "log_event", "check_session"]
```

## Example: Creating a C Authentication Harness

```bash
# 1. Create skeleton
mkdir harness-auth/
cd harness-auth/
cat > main.c << 'EOF'
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// Extracted and stubbed code will go here

int main(void) {
    // Test the authentication
    const char *user = "admin";
    int result = authenticate_user(user);
    printf("Auth result: %d\n", result);
    return 0;
}
EOF

# 2. Extract target function
claudit harness extract /path/to/project --functions authenticate_user > extracted.c
# Copy the extracted code into main.c

# 3. Try to compile
gcc -o harness main.c -Wall -Werror
# Error: undefined reference to `validate_credentials`

# 4. Analyze what's needed
claudit harness analyze-deps /path/to/project --functions authenticate_user
# Shows: validate_credentials, log_event, check_session are called

# 5. Extract critical dependency
claudit harness extract /path/to/project --functions validate_credentials >> main.c
# Error still: undefined reference to `check_database`

# 6. Stub out non-critical dependencies
claudit harness get-signature /path/to/project --function check_database
# Use signature to create stub:
cat >> main.c << 'EOF'
int check_database(const char *query) {
    // AUTO-GENERATED STUB - return success for testing
    return 1;
}
EOF

# 7. Compile again - SUCCESS!
gcc -o harness main.c -Wall -Werror
./harness
```

## Use Cases

### Security Auditing
Extract authentication/authorization functions and create isolated harnesses to test security properties without running the full application.

### Performance Testing
Extract performance-critical functions and create harnesses with realistic stubs to benchmark different inputs.

### Fuzzing
Extract parsing or validation functions and create harnesses suitable for fuzzing tools.

### Legacy Code Testing
Create test harnesses for untested legacy code without refactoring the entire codebase.

## Tips

- **Start small**: Extract just the target function first, then add dependencies as needed
- **Stub liberally**: Don't extract everything - stub I/O, logging, metrics, external services
- **Extract critical logic**: Do extract business logic, validation, calculations
- **Use compilation errors**: Let the compiler tell you what's missing
- **Check signatures**: Use `get-signature` to create accurate stubs
- **Iterate**: Don't expect the harness to work on first try - iterate based on errors
