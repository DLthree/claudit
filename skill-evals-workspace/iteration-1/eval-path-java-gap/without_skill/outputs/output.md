# Reachability Analysis: `createGroup` → `getByName` in sample-uaa

## Commands Run

1. Searched for all Java files in `/Users/dloffre/proj/claudit/sample-uaa` (via Glob).
2. Searched for all occurrences of `createGroup` in Java files (via Grep).
3. Searched for all occurrences of `getByName` in Java files (via Grep).
4. Read `ScimGroupEndpoints.java` (lines 1–100 and 340–510) to examine the `createGroup` method body and surrounding methods.
5. Read `ScimGroupProvisioning.java` to understand the interface definition.
6. Read `JdbcScimGroupProvisioning.java` (lines 140–280) to examine the `getByName` and `create` implementations.
7. Read `ScimAopConfig.java` to check for AOP advice triggered after `createGroup`.

## Relevant Source Files

- `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/endpoints/ScimGroupEndpoints.java`
- `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupProvisioning.java`
- `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/jdbc/JdbcScimGroupProvisioning.java`
- `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/beans/ScimAopConfig.java`

## Analysis

### `createGroup` (ScimGroupEndpoints, line 372)

```java
public ScimGroup createGroup(@RequestBody ScimGroup group, HttpServletResponse httpServletResponse) {
    group.setZoneId(identityZoneManager.getCurrentIdentityZoneId());
    ScimGroup created = dao.create(group, identityZoneManager.getCurrentIdentityZoneId());
    // ... adds members, calls membershipManager.getMembers ...
    return created;
}
```

The method calls `dao.create(...)` (where `dao` is a `ScimGroupProvisioning`), then `membershipManager.addMember(...)` and `membershipManager.getMembers(...)`. It does **not** call `dao.getByName(...)` directly.

### `dao.create` (JdbcScimGroupProvisioning, line 256)

The `create` implementation inserts a row via JDBC and then calls `retrieve(id, zoneId)`. It does **not** call `getByName`.

### Other paths considered

- `getGroupId` (ScimGroupEndpoints, line 345): calls `dao.getByName(...)` directly, but it is a private helper used by `addZoneManagers`, not by `createGroup`.
- `addZoneManagers` (ScimGroupEndpoints, line 479): calls `getGroupId(...)` (which calls `getByName`), and may call `createGroup(group, httpServletResponse)` on line 500 if the group is not found. This means the call direction is `addZoneManagers` → `createGroup`, not the other way around.
- `createOrGet` (JdbcScimGroupProvisioning, line 164): calls `getByName(...)`, but `createGroup` in `ScimGroupEndpoints` does not call `createOrGet`.
- `ScimAopConfig`: the `@AfterReturning` advice on `createGroup` (line 58) only calls `scimEventPublisher.groupCreated(group)`, not `getByName`.

### Call graph summary

```
createGroup (ScimGroupEndpoints)
  └─> dao.create (JdbcScimGroupProvisioning)
        └─> retrieve (JdbcScimGroupProvisioning)   [NOT getByName]
  └─> membershipManager.addMember (...)
  └─> membershipManager.getMembers (...)
```

`getByName` is reachable from `addZoneManagers` (via `getGroupId`) and from `createOrGet`, but neither of these are called from `createGroup`.

## Conclusion

**No, `getByName` is not reachable from `createGroup`.**

`createGroup` in `ScimGroupEndpoints` calls `dao.create(...)`, which in `JdbcScimGroupProvisioning` inserts the group and calls `retrieve(...)` — not `getByName`. The `getByName` method is available on the `ScimGroupProvisioning` interface and is called from other places in the codebase (e.g., `getGroupId`, `createOrGet`, `ScimGroupBootstrap`, `ScimUserBootstrap`), but none of those are reachable from `createGroup` in the production call path.

The only indirect connection is in the reverse direction: `addZoneManagers` calls `getByName` (via `getGroupId`) and may fall back to calling `createGroup`, but `createGroup` cannot reach `getByName`.
