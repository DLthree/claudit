# Test Harness Generation

Extract functions verbatim from source code and stub out their dependencies to create standalone test harnesses.

## When to use

Use this skill when the user asks:
- "Create a harness for function X"
- "Harness all the functions in file.c and stub out dependencies"
- "Extract the Spring filter chain and make it standalone"
- "Generate a test harness for these functions"
- "Create a standalone version of this code I can test"

## How to invoke

```bash
# Extract specific functions by name
claudit harness extract <project_dir> --functions func1,func2 [--language c|java|python]

# Extract all functions from a file
claudit harness extract <project_dir> --file path/to/file.c [--language c|java|python]

# Control stub depth and add main function
claudit harness extract <project_dir> --functions process --stub-depth 2 --include-main
```

```python
from claudit.skills.harness import extract_functions, extract_file

# Extract specific functions
result = extract_functions(
    "/path/to/project",
    ["authenticate_user", "validate_token"],
    language="c",
    stub_depth=1,
    include_main=True
)

# Extract all functions from a file
result = extract_file(
    "/path/to/project",
    "src/filters/security.c",
    language="c"
)
```

## Output format

```json
{
  "extracted": [
    {
      "function": "authenticate_user",
      "file": "auth.c",
      "start_line": 42,
      "end_line": 67,
      "source": "int authenticate_user(const char *username) {\n    ...\n}",
      "signature": "int authenticate_user(const char *username)"
    }
  ],
  "stubs": [
    {
      "function": "validate_credentials",
      "signature": "int validate_credentials(const char *user, const char *pass)",
      "stub_source": "int validate_credentials(const char *user, const char *pass) {\n    return 0;  /* AUTO-GENERATED STUB */\n}",
      "return_type": "int",
      "reason": "called_by authenticate_user",
      "original_file": "creds.c"
    }
  ],
  "includes": [
    "#include <stdio.h>",
    "#include <string.h>",
    "#include \"auth.h\""
  ],
  "complete_harness": "/* AUTO-GENERATED TEST HARNESS */\n\n#include <stdio.h>\n...",
  "language": "c",
  "stats": {
    "extracted_count": 1,
    "stub_count": 3,
    "total_lines": 120
  }
}
```

## Notes

- Target functions are extracted **verbatim** - no modifications to the original source
- Dependencies are identified using the call graph
- `--stub-depth` controls how many levels deep to analyze dependencies (default: 1)
- Stubs are minimal implementations that return default values (0, NULL, None, etc.)
- Auto-builds the index and call graph if they don't exist
- The `complete_harness` field contains ready-to-use code that can be compiled/run
- For Java methods, the harness includes necessary class wrapper code
- For Python, type information may be limited due to dynamic typing

## Use cases

### Security auditing
Extract security-critical functions (authentication, validation) and create isolated test harnesses to verify their behavior without running the full application.

### Legacy code testing
Take complex, tightly-coupled legacy code and create standalone harnesses for unit testing without refactoring the entire codebase.

### Framework extraction
Extract business logic from framework code (e.g., Spring filters, servlet handlers) and create standalone versions for faster testing.

### Dependency isolation
Isolate specific functions from their dependencies to test edge cases or perform fuzzing without side effects.
