# Security Audit: User Input Reachability to Database Save Operations

**Project:** `/Users/dloffre/proj/claudit/sample-uaa`
**Question:** Can user input from the REST layer reach the database save operations?
**Date:** 2026-03-11

---

## Commands Run

### Step 1: Initial path find

```bash
claudit path find createUser create /Users/dloffre/proj/claudit/sample-uaa --language java
```

**Result:**
```json
{
  "source": "createUser",
  "target": "create",
  "paths": [],
  "path_count": 0,
  "cache_used": true
}
```

Zero paths found. Triggering fallback workflow per skill instructions (Java interface→implementation edges are a known GNU Global limitation).

---

### Step 2: Fallback — inspect callees of source

```bash
claudit graph callees createUser /Users/dloffre/proj/claudit/sample-uaa
```

**Result:**
```json
{
  "function": "createUser",
  "callees": ["createUser"],
  "count": 1
}
```

Only a self-reference was returned — the call to `scimUserProvisioning.createUser(...)` (an interface call) was not resolved by the static call graph. This confirms the Java interface→implementation gap.

---

### Step 3: Fallback — inspect callers of target

```bash
claudit graph callers create /Users/dloffre/proj/claudit/sample-uaa
```

**Result:** 363 callers listed, including `JdbcScimUserProvisioning` and `ScimUserEndpointsMockMvcTests` — confirming `create` is a real database sink with multiple upstream callers.

---

### Step 4: Read source to confirm the missing edge

Read `ScimUserEndpoints.java` (lines 231–303) and `JdbcScimUserProvisioning.java` (lines 248–316).

---

### Step 5: Highlight confirmed path

```bash
claudit highlight path createUser createUser create \
  --project-dir /Users/dloffre/proj/claudit/sample-uaa --language java
```

Highlight output confirmed the hop list is recognized by the tool (resolved to closest matching definitions in the index).

---

## Paths Found

**0 paths** returned by `claudit path find` due to the Java interface→implementation limitation (GNU Global misses the `ScimUserProvisioning` interface → `JdbcScimUserProvisioning` implementation edge).

### Manually confirmed path (via source reading):

**Path 1 — Direct create (alias handling disabled):**

| Hop | Function | File | Line | Snippet |
|-----|----------|------|------|---------|
| 1 | `createUser` (REST handler) | `server/src/main/java/org/cloudfoundry/identity/uaa/scim/endpoints/ScimUserEndpoints.java` | 234 | `public ScimUser createUser(@RequestBody ScimUser user, ...)` |
| 2 | `scimUserProvisioning.createUser` (interface dispatch) | `ScimUserEndpoints.java` | 268 | `scimUser = scimUserProvisioning.createUser(user, user.getPassword(), ...)` |
| 3 | `createUser` (impl) | `server/src/main/java/org/cloudfoundry/identity/uaa/scim/jdbc/JdbcScimUserProvisioning.java` | 312 | `public ScimUser createUser(ScimUser user, final String password, String zoneId)` |
| 4 | `create` (DB write) | `JdbcScimUserProvisioning.java` | 315 | `return create(user, zoneId);` |
| 5 | `jdbcTemplate.update` | `JdbcScimUserProvisioning.java` | 266 | `jdbcTemplate.update(CREATE_USER_SQL, ps -> { ... ps.setString(5, user.getUserName()); ... })` |

**Path 2 — Transactional create with alias handling (alias enabled):**

| Hop | Function | File | Line | Snippet |
|-----|----------|------|------|---------|
| 1 | `createUser` (REST handler) | `ScimUserEndpoints.java` | 234 | `public ScimUser createUser(@RequestBody ScimUser user, ...)` |
| 2 | `createScimUserWithAliasHandling` | `ScimUserEndpoints.java` | 265 | `scimUser = createScimUserWithAliasHandling(user)` |
| 3 | `scimUserProvisioning.createUser` (interface dispatch) | `ScimUserEndpoints.java` | 286 | `scimUserProvisioning.createUser(user, user.getPassword(), ...)` |
| 4 | `createUser` (impl) | `JdbcScimUserProvisioning.java` | 312 | `public ScimUser createUser(...)` |
| 5 | `create` (DB write) | `JdbcScimUserProvisioning.java` | 315 | `return create(user, zoneId);` |
| 6 | `jdbcTemplate.update` | `JdbcScimUserProvisioning.java` | 266 | `jdbcTemplate.update(CREATE_USER_SQL, ps -> { ... })` |

---

## Conclusions About Reachability

**YES — user input from the REST layer can reach database save operations.**

### Confirmed execution path:

1. **REST Entry Point:** `POST /Users` is handled by `ScimUserEndpoints.createUser()`. The entire request body is deserialized into a `ScimUser` object via `@RequestBody`. Fields include `userName`, `emails`, `name.givenName`, `name.familyName`, `phoneNumbers`, `origin`, `externalId`, `aliasId`, `aliasZid`, `salt`, and `password`.

2. **Interface dispatch:** `scimUserProvisioning.createUser(user, user.getPassword(), zoneId)` is called. The `scimUserProvisioning` field is typed as `ScimUserProvisioning` (interface), which is why GNU Global failed to resolve the edge. At runtime, the implementation is `JdbcScimUserProvisioning`.

3. **Implementation:** `JdbcScimUserProvisioning.createUser()` encodes the password via `passwordEncoder.encode(password)` then calls `create(user, zoneId)`.

4. **Database write:** `create()` executes `jdbcTemplate.update(CREATE_USER_SQL, ...)` using a `PreparedStatement`. User-supplied fields are bound via `ps.setString()`/`ps.setBoolean()` — all through parameterized queries, which prevents SQL injection.

### Security observations:

- **SQL injection risk: NONE.** All database writes use `PreparedStatement` parameter binding (`ps.setString(...)`) via `JdbcTemplate.update()`. No string concatenation into SQL is performed.
- **Input validation exists:** `ScimUtils.validate(user)` is called before the database write. Password complexity is validated via `passwordValidator.validate()` for UAA-origin users.
- **Sanitization gaps (minor):** Fields like `externalId`, `aliasId`, `aliasZid`, and `salt` are written to the database with no explicit format validation — only a `hasText()` null check. These are trusted/internal fields in the UAA context, but any injection into those fields would be constrained by the prepared statement.
- **User limit enforcement:** `validateUserLimit(zoneId, userConfig)` is checked before the insert.
- **Origin validation:** `checkOrigin()` is called when `isCheckOriginEnabled(userConfig)` is true, preventing unauthorized origins.

### Summary:

User input from the REST `POST /Users` endpoint does reach `JdbcScimUserProvisioning.create()` and ultimately `jdbcTemplate.update()` (the database save). The path traverses an interface boundary (`ScimUserProvisioning`) that static analysis (GNU Global) cannot resolve, which is why `claudit path find` returned 0 paths. The actual risk is low: the code uses parameterized SQL throughout, and input validation is applied at the endpoint layer before the data reaches the database.
