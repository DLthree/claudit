# Security Audit: User Input Reachability to Database Save Operations
## Project: `/Users/dloffre/proj/claudit/sample-uaa`

---

## Commands / Files Examined

1. `ls /Users/dloffre/proj/claudit/sample-uaa/` — top-level project structure
2. `find ... -name "*.java" | grep -i "endpoint\|controller"` — enumerate REST controllers
3. Read: `server/src/main/java/org/cloudfoundry/identity/uaa/scim/endpoints/ScimUserEndpoints.java`
4. Read: `server/src/main/java/org/cloudfoundry/identity/uaa/scim/jdbc/JdbcScimUserProvisioning.java`
5. Read: `server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimUserProvisioning.java`
6. Read: `server/src/main/java/org/cloudfoundry/identity/uaa/resources/jdbc/AbstractQueryable.java`
7. Read: `server/src/main/java/org/cloudfoundry/identity/uaa/resources/jdbc/SearchQueryConverter.java`
8. Read: `server/src/main/java/org/cloudfoundry/identity/uaa/resources/jdbc/SimpleSearchQueryConverter.java`
9. Read: `server/src/main/java/org/cloudfoundry/identity/uaa/scim/util/ScimUtils.java`
10. Read: `server/src/main/java/org/cloudfoundry/identity/uaa/scim/endpoints/ChangeEmailEndpoints.java`
11. Read: `server/src/main/java/org/cloudfoundry/identity/uaa/zone/IdentityZoneEndpoints.java`

---

## Summary Answer: Yes — User Input Reaches Database Save Operations

User-controlled HTTP input flows directly into database write (INSERT/UPDATE/DELETE) operations through several distinct code paths. The paths are traced below.

---

## Traced Execution Paths

### Path 1: POST /Users — Create User

**Entry point:** `ScimUserEndpoints.createUser(@RequestBody ScimUser user, ...)`

- The request body is deserialized by Jackson into a `ScimUser` object.
- Fields `userName`, `emails`, `givenName`, `familyName`, `phoneNumbers`, `origin`, `externalId`, `aliasId`, `aliasZid`, `password`, `active`, `verified`, `salt` are all populated from user-supplied JSON.
- Validation steps applied:
  - `throwWhenUserManagementIsDisallowed(user.getOrigin(), request)` — checks internal user management flag
  - `ScimUtils.validate(user)` — checks username is non-empty and matches `[\p{L}+0-9+\-_.@'!]+` for UAA origin; checks exactly one email is present
  - `passwordValidator.validate(user.getPassword())` — password policy check (for UAA users only)
- All validated fields then flow to:

```
ScimUserProvisioning.createUser(user, password, zoneId)
  → JdbcScimUserProvisioning.createUser(user, password, zoneId)
    → user.setPassword(passwordEncoder.encode(password))   // bcrypt encode
    → JdbcScimUserProvisioning.create(user, zoneId)
      → jdbcTemplate.update(CREATE_USER_SQL, ...)
```

**Database write:** `INSERT INTO users (id, version, created, lastModified, username, email, givenName, familyName, active, phoneNumber, verified, origin, external_id, identity_zone_id, alias_id, alias_zid, salt, passwd_lastmodified, last_logon_success_time, previous_logon_success_time, password) VALUES (?, ?, ...)`

All user-supplied field values (`userName`, `email`, `givenName`, `familyName`, `phoneNumber`, `origin`, `externalId`, `aliasId`, `aliasZid`, `salt`) are passed as **parameterized JDBC PreparedStatement parameters** — they are not interpolated into the SQL string.

**SQL injection risk:** Low. The CREATE_USER_SQL is a static SQL template; all user data is bound via positional parameters (`ps.setString(...)`, `ps.setBoolean(...)`, etc.). No raw string concatenation of user values occurs in the SQL.

---

### Path 2: PUT /Users/{userId} — Update User

**Entry point:** `ScimUserEndpoints.updateUser(@RequestBody ScimUser user, @PathVariable String userId, ...)`

- The path variable `userId` and full `ScimUser` body are user-controlled.
- Validation steps applied:
  - `throwWhenUserManagementIsDisallowed(...)` — checks internal user management flag
  - `throwWhenInvalidSelfEdit(...)` — checks scopes for self-edit restrictions
  - ETag version check
  - `ScimUtils.validate(user)` called inside `JdbcScimUserProvisioning.update(...)`
- Call chain:

```
ScimUserService.updateUser(userId, user)
  → JdbcScimUserProvisioning.update(id, user, zoneId)
    → jdbcTemplate.update(UPDATE_USER_SQL, ...)
```

**Database write:** `UPDATE users SET version=?, lastModified=?, username=?, email=?, givenName=?, familyName=?, active=?, phoneNumber=?, verified=?, origin=?, external_id=?, salt=?, alias_id=?, alias_zid=? WHERE id=? AND version=? AND identity_zone_id=?`

Again, all user data is bound as positional parameters. The WHERE clause binds `id` (from path variable) and the zone ID from server context — these cannot be injected.

**SQL injection risk:** Low. PreparedStatement with positional parameters used throughout.

---

### Path 3: DELETE /Users/{userId} — Delete User

**Entry point:** `ScimUserEndpoints.deleteUser(@PathVariable String userId, ...)`

- `userId` is user-controlled (a path variable).
- Call chain:

```
JdbcScimUserProvisioning.delete(id, version, zoneId)
  → jdbcTemplate.update(DELETE_USER_SQL, userId, zoneId)
  OR jdbcTemplate.update(DELETE_USER_SQL + " and version=?", userId, zoneId, version)
```

**Database write:** `DELETE FROM users WHERE id=? AND identity_zone_id=?`

Parameterized query — not injectable.

---

### Path 4: GET /Users?filter=... — Query/Search Users

**Entry point:** `ScimUserEndpoints.findUsers(@RequestParam String filter, @RequestParam String sortBy, ...)`

- The `filter` and `sortBy` parameters are fully user-supplied query strings.
- Call chain:

```
scimUserProvisioning.query(filter, sortBy, ascending, zoneId)
  → AbstractQueryable.query(filter, sortBy, ascending, zoneId)
    → queryConverter.convert(filter, sortBy, ascending, zoneId)
       → SimpleSearchQueryConverter.convert(...)
          → SCIMFilter.parse(filter)           // SCIM filter parser (UnboundID SDK)
          → validateFilterAttributes(scimFilter, VALID_ATTRIBUTE_NAMES)  // allowlist check
          → whereClauseFromFilter(...)         // generates SQL WHERE fragment
             → comparisonClause(...)           // builds parameterized named params (:__xxx_0)
    → getQuerySQL(where)
       → "SELECT ... FROM users WHERE (" + where.getSql() + ")"
    → namedParameterJdbcTemplate.query(completeSql, where.getParams(), rowMapper)
```

**Key security mechanism:** The SCIM filter string is parsed by the UnboundID SCIM SDK's `SCIMFilter.parse()`, then validated against an allowlist of column names (`VALID_ATTRIBUTE_NAMES`). The filter values are placed into a named parameter map and bound via `NamedParameterJdbcTemplate` — they are NOT concatenated into the SQL string directly.

**Potential concern for `sortBy`:** The `sortBy` parameter flows through `queryConverter.map(sortBy)` and then is validated via `validateOrderBy()`, which compares it against the allowed fields in `USER_FIELDS`. It is then **string-concatenated** into the SQL ORDER BY clause: `whereClause += ORDER_BY + internalSortBy + (ascending ? " ASC" : " DESC")`. However, `validateOrderBy()` enforces an allowlist against `USER_FIELDS` before this concatenation occurs. Bypassing this would require the allowlist check to be defective.

**SQL injection risk for filter values:** Low — values are parameterized. **Risk for sortBy:** Moderate concern, allowlist-protected but relies on the correctness of the allowlist check.

---

### Path 5: PATCH /Users/{userId}/status — Account Status Update

**Entry point:** `ScimUserEndpoints.updateAccountStatus(@RequestBody UserAccountStatus status, @PathVariable String userId)`

- User sends JSON with `locked` and `passwordChangeRequired` fields.
- Validation: `locked=true` is rejected; `passwordChangeRequired=false` is rejected (only `true` allowed via API).
- Call chain if `passwordChangeRequired=true`:

```
scimUserProvisioning.updatePasswordChangeRequired(userId, true, zoneId)
  → JdbcScimUserProvisioning.updatePasswordChangeRequired(...)
    → jdbcTemplate.update(UPDATE_PASSWORD_CHANGE_REQUIRED_SQL, ps -> {
        ps.setBoolean(1, passwordChangeRequired);
        ps.setString(2, userId);
        ps.setString(3, zoneId);
    })
```

**Database write:** `UPDATE users SET passwd_change_required=? WHERE id=? AND identity_zone_id=?`

User input reaches a boolean column write. Fully parameterized.

---

### Path 6: POST /email_changes — Email Change Completion

**Entry point:** `ChangeEmailEndpoints.changeEmail(@RequestBody String code)`

- User submits a short-lived code (previously generated and stored).
- The code is retrieved from the server-side expiring code store (not user-controlled directly).
- The data inside the code (userId, email) was set at code-generation time, but the email value originally came from user input at `POST /email_verifications`.

```
expiringCodeStore.retrieveCode(code, zoneId)  // server-side lookup
→ scimUserProvisioning.update(userId, user, zoneId)
  → jdbcTemplate.update(UPDATE_USER_SQL, ...)
```

**Risk:** The actual DB write uses the email stored in the code store at generation time. The code lookup itself is parameterized. Risk is low, but the email value originally derived from user input (at `/email_verifications`) reaches the `email` and `username` columns.

---

## Conclusions

| Path | User Input Field(s) | Database Operation | SQL Injection Risk |
|------|--------------------|--------------------|-------------------|
| POST /Users | userName, email, givenName, familyName, phoneNumber, origin, externalId, password, aliasId, aliasZid, salt | INSERT into `users` | Low (PreparedStatement) |
| PUT /Users/{id} | Same fields + path var `userId` | UPDATE `users` | Low (PreparedStatement) |
| PATCH /Users/{id} | Path var `userId` | UPDATE `users` | Low (PreparedStatement) |
| DELETE /Users/{id} | Path var `userId` | DELETE from `users` | Low (PreparedStatement) |
| GET /Users?filter=&sortBy= | `filter` query param, `sortBy` query param | SELECT from `users` | Low for filter (parameterized); `sortBy` relies on allowlist before string concatenation into ORDER BY |
| PATCH /Users/{id}/status | `passwordChangeRequired` boolean, path var `userId` | UPDATE `users` | Low (PreparedStatement) |
| POST /email_changes | one-time `code` string (indirect—email stored in code) | UPDATE `users` | Low (PreparedStatement) |

### Overall Assessment

**Yes — user input from the REST layer reaches every category of database save operation** (INSERT, UPDATE, DELETE). The application uses parameterized queries (Spring's `JdbcTemplate` with `PreparedStatement`) consistently for all write operations, which prevents classic SQL injection for field values.

**The most notable attention point** is the `sortBy` query parameter in `GET /Users`. The SCIM filter parser converts user filter values to named parameters, but `sortBy` is first mapped through `validateOrderBy()` (allowlist check against `USER_FIELDS`) and then **string-concatenated** into the ORDER BY clause. If `validateOrderBy()` were bypassed or had a flaw, an ORDER BY injection could be possible. The allowlist is validated before concatenation, which mitigates this, but it is the single code path where user-derived text is placed directly into the SQL string.

**Passwords** are bcrypt-encoded before being written to the database; they are never stored in plaintext.

**No unparameterized SQL construction from user input** was found in the write paths reviewed.
