# Call Graph Analysis: `createScimGroup` in sample-uaa

## Commands Run

### 1. Build the call graph
```
claudit graph build /Users/dloffre/proj/claudit/sample-uaa --language java
```
Result:
```json
{
  "status": "cached",
  "node_count": 11902,
  "edge_count": 100580,
  "language": "java",
  "project_dir": "/Users/dloffre/proj/claudit/sample-uaa"
}
```

### 2. Query callees of `createScimGroup`
```
claudit graph callees createScimGroup /Users/dloffre/proj/claudit/sample-uaa
```
Result:
```json
{
  "function": "createScimGroup",
  "callees": [],
  "count": 0
}
```

### 3. Query callers of `createScimGroup` (to find context)
```
claudit graph callers createScimGroup /Users/dloffre/proj/claudit/sample-uaa
```
Result:
```json
{
  "function": "createScimGroup",
  "callers": [],
  "count": 0
}
```

## Findings

The static call graph returned 0 callees and 0 callers for `createScimGroup`. This is consistent with the known limitation that GNU Global misses certain Java edges, and also reflects an important finding about the name itself (see below).

### Source Investigation

Per the workaround workflow (read the implementation class when static analysis returns 0 results), I searched the codebase for `createScimGroup`:

**File:** `/Users/dloffre/proj/claudit/sample-uaa/uaa/src/test/java/org/cloudfoundry/identity/uaa/scim/endpoints/ScimGroupEndpointDocs.java`

**Key finding:** `createScimGroup` is **not a method** in this codebase. It appears only as a **string literal** passed to the `document(...)` call on line 130:

```java
ResultActions createResult = createScimGroupHelper(scimGroup)
        .andDo(document("{ClassName}/createScimGroup",
                ...));
```

The string `"createScimGroup"` is a documentation snippet name (Spring REST Docs naming convention). It is not a callable function, which explains why the call graph returns no results.

### The actual method: `createScimGroupHelper`

The nearby private method `createScimGroupHelper` (line 396) is the real implementation that creates SCIM groups. It calls:

| Callee | Description |
|---|---|
| `post("/Groups")` | Builds an HTTP POST request to the `/Groups` endpoint |
| `.header("Authorization", ...)` | Adds an Authorization header with the scim.write token |
| `.contentType(APPLICATION_JSON)` | Sets content type |
| `.content(serializeWithoutMeta(scimGroup))` | Serializes the ScimGroup object |
| `mockMvc.perform(post)` | Executes the mock HTTP request |
| `.andExpect(status().isCreated())` | Asserts HTTP 201 Created response |

This method is called from the test method `createRetrieveUpdateListScimGroup()` at line 117.

## Notes on the Call Graph

- The graph was already cached (11,902 nodes, 100,580 edges), so `graph build` returned immediately.
- `--language` flag is only valid for `graph build`, not for `graph callees` or `graph callers` (per skill instructions).
- The 0-result outcome for `createScimGroup` is due to the name being a string literal in test documentation code, not an actual Java method definition.
- GNU Global's known limitation (missing Java interface → implementation edges) was not the cause here; the function simply does not exist as a callable method.
