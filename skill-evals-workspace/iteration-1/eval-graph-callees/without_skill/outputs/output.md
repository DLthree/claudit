# Call Relationships for `createScimGroup` in sample-uaa

## Overview

The name `createScimGroup` appears in two contexts in the codebase:

1. As a documentation label (`{ClassName}/createScimGroup`) used with Spring REST Docs in a test.
2. As the private helper method `createScimGroupHelper(ScimGroup)` that performs the actual group creation HTTP call.

The relevant code lives in:
`/Users/dloffre/proj/claudit/sample-uaa/uaa/src/test/java/org/cloudfoundry/identity/uaa/scim/endpoints/ScimGroupEndpointDocs.java`

---

## Commands Run

```
# Find all files containing "createScimGroup"
grep -r createScimGroup /Users/dloffre/proj/claudit/sample-uaa --include="*.java" -n

# Read the full file to understand the call graph
# (Read tool on ScimGroupEndpointDocs.java)
```

---

## Call Graph

### `createRetrieveUpdateListScimGroup()` (the `@Test` method) calls:

- `newScimUser()` — creates a SCIM user for use as a group member
- `createScimGroupHelper(scimGroup)` — sends POST /Groups and returns ResultActions
  - (chained) `.andDo(document("{ClassName}/createScimGroup", ...))` — records REST Docs snippets

### `createScimGroupHelper(ScimGroup scimGroup)` calls:

| Callee | Description |
|--------|-------------|
| `post("/Groups")` | Builds a `MockHttpServletRequestBuilder` for POST /Groups (Spring MVC Test) |
| `.header("Authorization", "Bearer " + scimWriteToken)` | Attaches the OAuth bearer token header |
| `.contentType(APPLICATION_JSON)` | Sets Content-Type to application/json |
| `.content(serializeWithoutMeta(scimGroup))` | Sets the request body |
| `serializeWithoutMeta(scimGroup)` | Serializes the ScimGroup, stripping `id`, `zoneId`, `meta`, `schemas` fields |
| `mockMvc.perform(post)` | Executes the HTTP request via Spring MockMvc |
| `.andExpect(status().isCreated())` | Asserts HTTP 201 Created response |

### `serializeWithoutMeta(ScimGroup scimGroup)` calls:

| Callee | Description |
|--------|-------------|
| `JsonUtils.writeValueAsString(scimGroup)` | Serializes ScimGroup to JSON string |
| `JsonUtils.readValue(..., new TypeReference<Map<String, Object>>(){})` | Deserializes JSON into a Map |
| `content.remove("id")` | Strips the `id` field |
| `content.remove("zoneId")` | Strips the `zoneId` field |
| `content.remove("meta")` | Strips the `meta` field |
| `content.remove("schemas")` | Strips the `schemas` field |
| `JsonUtils.writeValueAsString(content)` | Re-serializes the stripped Map to JSON |

### `newScimUser()` calls (used to set up the group member):

| Callee | Description |
|--------|-------------|
| `generator.generate()` | Generates a random alphanumeric username |
| `new ScimUser(...)` | Constructs a ScimUser object |
| `member.setPassword(...)` | Sets the user password |
| `member.setPrimaryEmail(...)` | Sets the user email |
| `MockMvcUtils.createUser(mockMvc, scimWriteToken, member)` | POSTs the new user via MockMvc and returns the created ScimUser |

---

## Summary of Direct Callees of `createScimGroupHelper`

1. `post("/Groups")` (Spring REST Docs MockMvcRestDocumentationRequestBuilders)
2. `serializeWithoutMeta(scimGroup)` (private helper in same class)
3. `mockMvc.perform(post)` (Spring MockMvc)
4. `status().isCreated()` (Spring MVC Test matchers)
5. `.andExpect(...)` (ResultActions)

The method essentially: serializes the ScimGroup (excluding metadata fields), builds a POST request to `/Groups` with the scimWriteToken, executes it via MockMvc, and asserts a 201 Created response is returned.
