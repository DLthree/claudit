# Harness Workflow Example

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
