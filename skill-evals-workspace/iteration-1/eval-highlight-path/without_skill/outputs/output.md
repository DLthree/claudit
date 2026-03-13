# Call Chain Analysis: createScimGroup → validateGroup → save

## Approach

Searched the `/Users/dloffre/proj/claudit/sample-uaa` codebase for the three functions mentioned using `Grep` and `Read` tools. Located the relevant source files and traced the call chain through the production code.

## Commands Run

1. `Grep pattern="createScimGroup" path=sample-uaa output_mode=files_with_matches` — found references in test/docs files
2. `Grep pattern="validateGroup" path=sample-uaa output_mode=files_with_matches` — found the main source in `JdbcScimGroupProvisioning.java`
3. `Read /Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/jdbc/JdbcScimGroupProvisioning.java` — read the full provisioning class
4. `Glob pattern="**/ScimGroupEndpoints.java"` — located the endpoint class
5. `Read /Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/endpoints/ScimGroupEndpoints.java` — read the full endpoint class

## Call Chain

The call chain spans two source files:

### File 1: ScimGroupEndpoints.java
**Path:** `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/endpoints/ScimGroupEndpoints.java`

#### Function 1: `createGroup` (the "createScimGroup" endpoint) — Lines 369–393

```java
@PostMapping({"/Groups", "/Groups/"})
@ResponseStatus(HttpStatus.CREATED)
@ResponseBody
public ScimGroup createGroup(@RequestBody ScimGroup group, HttpServletResponse httpServletResponse) {
    group.setZoneId(identityZoneManager.getCurrentIdentityZoneId());
    ScimGroup created = dao.create(group, identityZoneManager.getCurrentIdentityZoneId());
    if (group.getMembers() != null) {
        for (ScimGroupMember member : group.getMembers()) {
            try {
                membershipManager.addMember(created.getId(),
                        member,
                        identityZoneManager.getCurrentIdentityZoneId());
            } catch (ScimException ex) {
                logger.warn("Attempt to add invalid member: {} to group: {}", member.getMemberId(), created.getId(), ex);
                dao.delete(created.getId(), created.getVersion(), identityZoneManager.getCurrentIdentityZoneId());
                throw new InvalidScimResourceException("Invalid group member: " + member.getMemberId());
            }
        }
    }
    created.setMembers(membershipManager.getMembers(created.getId(),
            false,
            identityZoneManager.getCurrentIdentityZoneId()));
    addETagHeader(httpServletResponse, created);
    return created;
}
```

This is the HTTP POST handler for `/Groups`. It is labeled `createScimGroup` in the REST API documentation (see `ScimGroupEndpointDocs.java` line 130: `.andDo(document("{ClassName}/createScimGroup", ...))`). It delegates to `dao.create(...)`.

---

### File 2: JdbcScimGroupProvisioning.java
**Path:** `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/jdbc/JdbcScimGroupProvisioning.java`

#### Function 2: `create` (called by createGroup, calls validateGroup) — Lines 256–278

```java
@Override
public ScimGroup create(final ScimGroup group, final String zoneId) throws InvalidScimResourceException {
    validateZoneId(zoneId);
    validateAllowedUserGroups(zoneId, group);
    final String id = UUID.randomUUID().toString();
    logger.debug("creating new group with id: {}", id);
    try {
        validateGroup(group);
        jdbcTemplate.update(addGroupSql, ps -> {
            int pos = 1;
            ps.setString(pos++, id);
            ps.setString(pos++, group.getDisplayName());
            ps.setString(pos++, group.getDescription());
            ps.setTimestamp(pos++, new Timestamp(new Date().getTime()));
            ps.setTimestamp(pos++, new Timestamp(new Date().getTime()));
            ps.setInt(pos++, group.getVersion());
            ps.setString(pos, zoneId);
        });
    } catch (DuplicateKeyException ex) {
        throw new ScimResourceAlreadyExistsException("A group with displayName: " + group.getDisplayName()
                + " already exists.");
    }
    return retrieve(id, zoneId);
}
```

This calls `validateGroup(group)` on line 262, then performs the database write ("save") via `jdbcTemplate.update(addGroupSql, ...)` on line 263.

#### Function 3: `validateGroup` (called by create, guards the "save") — Lines 346–348

```java
private void validateGroup(ScimGroup group) throws ScimResourceConstraintFailedException {
    validateZoneId(group.getZoneId());
}
```

This is the validation gate called immediately before the database insert. It validates that the group's zoneId is present. If validation passes, `create()` proceeds to call `jdbcTemplate.update(addGroupSql, ...)` — the actual "save" to the database.

---

## Summary of the Call Chain

```
HTTP POST /Groups
    └─> ScimGroupEndpoints.createGroup()          [ScimGroupEndpoints.java:372]
            └─> dao.create()
                    └─> JdbcScimGroupProvisioning.create()   [JdbcScimGroupProvisioning.java:256]
                            └─> validateGroup()              [JdbcScimGroupProvisioning.java:262 → 346]
                            └─> jdbcTemplate.update(addGroupSql, ...) [JdbcScimGroupProvisioning.java:263]
                                    (the "save" — SQL INSERT into the groups table)
```

Note: There is no method literally named `save` in this codebase for SCIM groups. The "save" in the call chain description refers to `jdbcTemplate.update(addGroupSql, ...)` — the JDBC INSERT statement that persists the group record. The `validateGroup` method is called immediately before this persist step within the `create` method.

## Key File Locations

- **ScimGroupEndpoints.java** (createGroup / "createScimGroup"): `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/endpoints/ScimGroupEndpoints.java`
- **JdbcScimGroupProvisioning.java** (create, validateGroup, "save"): `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/jdbc/JdbcScimGroupProvisioning.java`
