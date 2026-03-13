# createScimGroup Function Extraction — Security Testing Analysis

## Approach Taken

1. Searched for all occurrences of `createScimGroup` in the sample-uaa codebase using grep/glob.
2. Read the primary source file containing the function and all directly referenced classes.
3. Traced the call chain from the test helper `createScimGroupHelper` up through the production endpoint `ScimGroupEndpoints.createGroup`, and down through the persistence layer.
4. Read the Spring Security configuration to understand the authorization model.
5. No files were created beyond this summary; no commands were run against a live system.

---

## Where the Function Lives

There are two related functions:

### 1. Test helper `createScimGroupHelper` (private, in test code)

**File:** `/Users/dloffre/proj/claudit/sample-uaa/uaa/src/test/java/org/cloudfoundry/identity/uaa/scim/endpoints/ScimGroupEndpointDocs.java` (lines 396–403)

```java
private ResultActions createScimGroupHelper(ScimGroup scimGroup) throws Exception {
    MockHttpServletRequestBuilder post = post("/Groups")
            .header("Authorization", "Bearer " + scimWriteToken)
            .contentType(APPLICATION_JSON)
            .content(serializeWithoutMeta(scimGroup));

    return mockMvc.perform(post).andExpect(status().isCreated());
}
```

This is a Spring MockMvc test helper that POSTs JSON to the `/Groups` endpoint. It is called by the `@Test createRetrieveUpdateListScimGroup` method at line 129.

### 2. Production endpoint `createGroup` (the actual implementation)

**File:** `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/endpoints/ScimGroupEndpoints.java` (lines 369–393)

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
                membershipManager.addMember(created.getId(), member,
                        identityZoneManager.getCurrentIdentityZoneId());
            } catch (ScimException ex) {
                logger.warn("Attempt to add invalid member: {} to group: {}",
                        member.getMemberId(), created.getId(), ex);
                dao.delete(created.getId(), created.getVersion(),
                        identityZoneManager.getCurrentIdentityZoneId());
                throw new InvalidScimResourceException("Invalid group member: " + member.getMemberId());
            }
        }
    }
    created.setMembers(membershipManager.getMembers(created.getId(), false,
            identityZoneManager.getCurrentIdentityZoneId()));
    addETagHeader(httpServletResponse, created);
    return created;
}
```

---

## Full Dependency Tree

### Data Model Classes (all in `model/` subproject)

| Class | File | Role |
|---|---|---|
| `ScimGroup` | `model/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroup.java` | Main entity: `displayName`, `description`, `members`, `zoneId` |
| `ScimCore<T>` | `model/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimCore.java` | Abstract base; holds `id`, `externalId`, `meta` (ScimMeta) |
| `ScimMeta` | `model/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimMeta.java` | Metadata: `version`, `created`, `lastModified`, `attributes` |
| `ScimGroupMember<TEntity>` | `model/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupMember.java` | Membership link; holds `memberId` (`value`), `type` (USER/GROUP), `origin`, `operation` |

### Service / Repository Interfaces (in `server/` subproject)

| Interface | File | Role |
|---|---|---|
| `ScimGroupProvisioning` | `server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupProvisioning.java` | Extends `ResourceManager<ScimGroup>` and `Queryable<ScimGroup>`; CRUD + `createOrGet` + `getByName` |
| `ScimGroupMembershipManager` | `server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupMembershipManager.java` | Manages group membership: `addMember`, `getMembers`, `removeMemberById`, etc. |

### JDBC Implementations (in `server/` subproject)

| Class | File | Role |
|---|---|---|
| `JdbcScimGroupProvisioning` | `server/src/main/java/org/cloudfoundry/identity/uaa/scim/jdbc/JdbcScimGroupProvisioning.java` | Implements `ScimGroupProvisioning`; writes to `groups` table; validates zone and allowed groups |
| `JdbcScimGroupMembershipManager` | `server/src/main/java/org/cloudfoundry/identity/uaa/scim/jdbc/JdbcScimGroupMembershipManager.java` | Implements membership management against `group_membership` table |

### Controller (in `server/` subproject)

| Class | File | Role |
|---|---|---|
| `ScimGroupEndpoints` | `server/src/main/java/org/cloudfoundry/identity/uaa/scim/endpoints/ScimGroupEndpoints.java` | Spring `@Controller`; injects `ScimGroupProvisioning`, `ScimGroupMembershipManager`, `IdentityZoneManager` |

### Test Infrastructure (in `uaa/` subproject, test scope)

| Class | File | Role |
|---|---|---|
| `ScimGroupEndpointDocs` | `uaa/src/test/java/org/cloudfoundry/identity/uaa/scim/endpoints/ScimGroupEndpointDocs.java` | Contains the `createScimGroupHelper` wrapper and the `@Test` that calls it |
| `EndpointDocs` | `uaa/src/test/java/org/cloudfoundry/identity/uaa/mock/EndpointDocs.java` | Base class: sets up `MockMvc` with a full `WebApplicationContext` and Spring Security filter chain |
| `MockMvcUtils` | `uaa/src/test/java/org/cloudfoundry/identity/uaa/mock/util/MockMvcUtils.java` | Provides `getClientCredentialsOAuthAccessToken` (POSTs to `/oauth/token`) and `createUser` |
| `AlphanumericRandomValueStringGenerator` | `server/src/main/java/org/cloudfoundry/identity/uaa/util/AlphanumericRandomValueStringGenerator.java` | Generates random alphanumeric usernames for test users |
| `DefaultTestContext` (annotation) | `uaa/src/test/java/org/cloudfoundry/identity/uaa/DefaultTestContext.java` | Boots the full UAA Spring context (`UaaBootConfiguration`) with an in-memory mock servlet |

---

## Authorization Model (Security Configuration)

**File:** `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/beans/ScimSecurityConfiguration.java`

The `groupEndpointSecurity` bean secures `/Groups` and `/Groups/**`:

| HTTP Method | Path | Required Scope / Role |
|---|---|---|
| `POST` | `/Groups` | `scim.write` OR zone admin |
| `POST` | `/Groups/**` | `scim.write` OR `groups.update` OR zone admin |
| `GET` | `/Groups/**` | `scim.read` OR zone admin |
| `PUT` | `/Groups/**` | `scim.write` OR `groups.update` OR zone admin |
| `PATCH` | `/Groups/**` | `scim.write` OR `groups.update` OR zone admin |
| `DELETE` | `/Groups/**` | `scim.write` OR zone admin |

All requests are authenticated via an `OAuth2AuthenticationProcessingFilter` that validates Bearer tokens using `UaaTokenServices`.

---

## Standalone HTTP Request to Reproduce createScimGroup

The simplest way to exercise the production `createGroup` logic without the test framework is a direct HTTP call to a running UAA instance:

### Step 1 — Obtain a token with `scim.write` scope

```
POST /oauth/token
Authorization: Basic YWRtaW46YWRtaW5zZWNyZXQ=   # admin:adminsecret (base64)
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=admin&scope=scim.write&revocable=true
```

### Step 2 — Create a SCIM group

```
POST /Groups
Authorization: Bearer <token_from_step_1>
Content-Type: application/json

{
  "displayName": "my-security-test-group",
  "description": "Created for security testing",
  "members": [
    {
      "value": "<valid-user-id>",
      "type": "USER",
      "origin": "uaa"
    }
  ]
}
```

**Expected 201 Created response fields:**

| Field | Description |
|---|---|
| `id` | UUID assigned by the server |
| `displayName` | Echo of the request value; must be unique per zone |
| `description` | Echo of the request value |
| `members[].value` | Member user/group UUID |
| `members[].type` | `USER` or `GROUP` |
| `members[].origin` | IDP alias (`uaa` for internal users) |
| `zoneId` | Identity zone the group was created in |
| `meta.version` | Optimistic-lock version (starts at 0) |
| `meta.created` | ISO-8601 timestamp |
| `meta.lastModified` | ISO-8601 timestamp |
| `schemas` | Always `["urn:scim:schemas:core:1.0"]` |

---

## Key Security Observations for Testing

1. **`displayName` uniqueness per zone** — `JdbcScimGroupProvisioning.create` throws `ScimResourceAlreadyExistsException` (→ HTTP 409) on duplicate `displayName` within the same `identity_zone_id`. Test: submit the same `displayName` twice.

2. **Allowed-groups allow-list** — `validateAllowedUserGroups` checks `IdentityZone.config.userConfig.resultingAllowedGroups()`. If the zone has a non-null allow-list, a `displayName` not on that list is rejected (`InvalidScimResourceException` → HTTP 400). Test: supply a `displayName` not in the zone's allow-list.

3. **Member validation and rollback** — If any member ID is invalid, the freshly-created group is immediately deleted (`dao.delete(...)`) before the 400 is returned. There is a brief window where the group exists in the DB; test for race conditions with concurrent reads.

4. **Zone injection** — `group.setZoneId(identityZoneManager.getCurrentIdentityZoneId())` overwrites any client-supplied `zoneId`. The zone is derived from the `X-Identity-Zone-Id` or `X-Identity-Zone-Subdomain` request header (via `IdentityZoneSwitchingFilter`). Test: supply a spoofed `zoneId` in the request body; verify it is ignored.

5. **No `displayName` length validation in the endpoint** — `validateGroup` in `JdbcScimGroupProvisioning` only checks that `zoneId` is non-blank. Test: extremely long `displayName` strings.

6. **`serializeWithoutMeta` in tests strips `id`, `zoneId`, `meta`, `schemas`** — In production the client may supply these fields; the server ignores `zoneId` (see point 4) but other supplied fields may be deserialized into the `ScimGroup` object. Test: supply unexpected fields.

---

## Files Created

None. This is a read-only analysis.

## Commands Run

No shell commands were executed against a live system. All analysis was performed by reading source files in `/Users/dloffre/proj/claudit/sample-uaa/`.
