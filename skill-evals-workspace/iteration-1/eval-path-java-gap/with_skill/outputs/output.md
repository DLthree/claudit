# Path Reachability: `createGroup` → `getByName` in sample-uaa

## Commands Run

### Step 1: Initial path find

```
claudit path find createGroup getByName /Users/dloffre/proj/claudit/sample-uaa --language java
```

**Result:**
```json
{
  "source": "createGroup",
  "target": "getByName",
  "paths": [],
  "path_count": 0,
  "cache_used": true
}
```

Path count: **0**. Fallback workflow triggered.

---

### Step 2: Fallback — inspect callees of `createGroup`

```
claudit graph callees createGroup /Users/dloffre/proj/claudit/sample-uaa
```

**Result:** 14 callees, including `create`, `addMember`, `getMembers`, `delete`, `warn`, etc.

Notable callee: **`create`** — `createGroup` (in `ScimGroupEndpoints`) calls `dao.create(group, ...)` on line 374.

---

### Step 3: Fallback — inspect callers of `getByName`

```
claudit graph callers getByName /Users/dloffre/proj/claudit/sample-uaa
```

**Result:** 28 callers, including `ScimGroupProvisioning`, `JdbcScimGroupProvisioning`, `ScimGroupBootstrap`, `ZoneSeeder`, `createOrGet`, and many test classes.

Notable caller: **`createOrGet`** — `JdbcScimGroupProvisioning.createOrGet` calls `getByName` (lines 166, 169), but `createOrGet` is NOT called by `createGroup`.

---

### Step 4: Source code verification

**`ScimGroupEndpoints.createGroup`** (`server/src/main/java/.../scim/endpoints/ScimGroupEndpoints.java`, line 372):
- Declares `private final ScimGroupProvisioning dao;` — typed to the **interface**
- Calls `dao.create(group, identityZoneManager.getCurrentIdentityZoneId())` (line 374)
- Does NOT call `dao.createOrGet(...)` or `dao.getByName(...)`

**`JdbcScimGroupProvisioning.create`** (`server/src/main/java/.../scim/jdbc/JdbcScimGroupProvisioning.java`, line 256):
- The concrete implementation of `ResourceManager.create`
- Performs a direct JDBC INSERT, then calls `retrieve(id, zoneId)` — does NOT call `getByName`

**`JdbcScimGroupProvisioning.createOrGet`** (lines 164–169):
- This method DOES call `getByName`, but is a separate entry point (`ScimGroupProvisioning.createOrGet`)
- `createGroup` never calls `createOrGet`

---

## Whether Path Was Found

**No path was found.** `path find` correctly returned 0 paths.

After manual source inspection, the 0-path result is confirmed to be **accurate**: there is genuinely no call chain from `createGroup` to `getByName` at runtime.

---

## Fallback Steps Taken

1. Ran `claudit path find createGroup getByName` — received 0 paths.
2. Ran `claudit graph callees createGroup` — identified `create` as the key callee.
3. Ran `claudit graph callers getByName` — found `createOrGet` as the nearest caller, not reachable from `createGroup`.
4. Read source of `ScimGroupEndpoints.createGroup` and `JdbcScimGroupProvisioning.create` to confirm no link exists.

---

## Java Interface/Impl Gap Explanation

The skill notes that GNU Global can miss edges across Java **interface → implementation** boundaries. In this codebase:

- `ScimGroupProvisioning` is an **interface** declaring `create(...)`, `createOrGet(...)`, and `getByName(...)`.
- `JdbcScimGroupProvisioning` is the concrete **implementation**.
- `ScimGroupEndpoints.createGroup` calls `dao.create(...)` where `dao` is typed as `ScimGroupProvisioning` (the interface).

GNU Global may fail to link the call `dao.create(...)` (on the interface) to `JdbcScimGroupProvisioning.create(...)` (the implementation), which is why the static call graph cannot trace the chain. However, in this specific case, the 0-path result is correct: even resolving the interface → impl gap, `JdbcScimGroupProvisioning.create` does not call `getByName`. The `getByName` method is only reachable via `createOrGet`, which is a separate code path not invoked by `createGroup`.

---

## Conclusion

`getByName` is **NOT reachable** from `createGroup`. The call path does not exist. The result from `claudit path find` (0 paths) is accurate and is not a false negative caused by the interface/impl gap — source inspection confirms the implementations do not form a chain.
