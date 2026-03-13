# Call Graph Analysis: `save` Method Callers in sample-uaa

## Commands Run

### 1. Build the call graph
```bash
claudit graph build /Users/dloffre/proj/claudit/sample-uaa --language java
```
**Result:**
```json
{
  "status": "cached",
  "node_count": 11902,
  "edge_count": 100580,
  "language": "java",
  "project_dir": "/Users/dloffre/proj/claudit/sample-uaa"
}
```

### 2. Query callers of `save`
```bash
claudit graph callers save /Users/dloffre/proj/claudit/sample-uaa
```
**Result:**
```json
{
  "function": "save",
  "callers": [],
  "count": 0
}
```

### 3. Query callees of `save` (to confirm it exists in the graph)
```bash
claudit graph callees save /Users/dloffre/proj/claudit/sample-uaa
```
**Result:**
```json
{
  "function": "save",
  "callees": [],
  "count": 0
}
```

---

## Findings: `save` Does Not Exist in sample-uaa

The `save` method returned zero callers and zero callees. A source-level search confirmed that the word `save` as a method name does not appear in the Java source files of this project. The only occurrences of "save" in the codebase are:
- Comments and documentation (e.g., `// Cache statically to save time`)
- References to Spring Security's `SavedRequest` class (a framework type, not a UAA persistence method)

**This is not a case of the known Java interface→implementation limitation in GNU Global.** The method simply does not exist by that name.

---

## Actual Data Persistence Entry Points

The sample-uaa project uses its own provisioning/DAO pattern (not Spring Data `save()`). The true persistence entry points are `create`, `update`, `upsert`, `storeAccessToken`, and `storeRefreshToken`. The following analysis identifies the real entry points.

### Additional commands run to find actual persistence entry points

```bash
claudit graph callers createUser /Users/dloffre/proj/claudit/sample-uaa
claudit graph callers storeAccessToken /Users/dloffre/proj/claudit/sample-uaa
claudit graph callers storeRefreshToken /Users/dloffre/proj/claudit/sample-uaa
claudit graph callers upsert /Users/dloffre/proj/claudit/sample-uaa
claudit graph callers persistRevocableToken /Users/dloffre/proj/claudit/sample-uaa
claudit graph callers createAccessToken /Users/dloffre/proj/claudit/sample-uaa
claudit graph callers create /Users/dloffre/proj/claudit/sample-uaa
claudit graph callees JdbcScimUserProvisioning /Users/dloffre/proj/claudit/sample-uaa
claudit graph callees JdbcRevocableTokenProvisioning /Users/dloffre/proj/claudit/sample-uaa
```

---

## Data Persistence Entry Points by Domain

### 1. User Persistence — `ScimUserProvisioning.createUser`
**Callers (production code, non-test):** 252 total callers found. Key production entry points:

| Caller | Role |
|---|---|
| `ScimUserEndpoints` | REST endpoint: `POST /Users` — creates users via SCIM API |
| `EmailAccountCreationService` | Self-registration flow — creates user on email activation |
| `InvitationsEndpoint` | Creates users when an invitation is accepted |
| `ScimUserBootstrap` | Bootstraps initial users from config at startup |
| `ScimUserAliasHandler` | Creates alias users across identity zones |
| `JdbcScimUserProvisioning` | JDBC implementation that executes the SQL INSERT |

**Implementation:** `JdbcScimUserProvisioning.createUser` issues the SQL INSERT. It is ultimately triggered via these REST paths:
- `POST /Users` → `ScimUserEndpoints.createUser`
- `POST /invitations/accept` → `InvitationsEndpoint` → `createUser`
- `POST /create_account` → `EmailAccountCreationService` → `createUser`

---

### 2. Token Persistence — `UaaTokenServices.persistRevocableToken` / `storeAccessToken`

**`storeAccessToken` callers (production):**

| Caller | Role |
|---|---|
| `DefaultTokenServices` | Core token service — stores access token on grant |
| `InMemoryTokenStore` | In-memory token store implementation |

**`persistRevocableToken` callers (production):**

| Caller | Role |
|---|---|
| `UaaTokenServices` | UAA-specific token service — persists revocable tokens |
| `createAccessToken` | Called during every OAuth2 token grant flow |

**`storeRefreshToken` callers (production):**

| Caller | Role |
|---|---|
| `DefaultTokenServices` | Stores refresh token when issuing new token pair |
| `InMemoryTokenStore` | In-memory implementation |

**Implementation:** `JdbcRevocableTokenProvisioning.upsert` executes the actual SQL UPSERT for revocable tokens. It is called by `UaaTokenServices.persistRevocableToken`.

**`upsert` callers (production):**

| Caller | Role |
|---|---|
| `UaaTokenServices` | Calls `upsert` via `RevocableTokenProvisioning` interface |
| `JdbcRevocableTokenProvisioning` | Self-call (create path delegates to upsert) |

**Token grant entry points that trigger persistence:**
- Any OAuth2 grant flow → `AbstractTokenGranter` → `createAccessToken` → `UaaTokenServices.createAccessToken` → `persistRevocableToken` → `JdbcRevocableTokenProvisioning.upsert`

---

### 3. Identity Provider Persistence — `IdentityProviderProvisioning.create`

**Key production callers of `create`:**

| Caller | Role |
|---|---|
| `IdentityProviderEndpoints` | REST endpoint: `POST /identity-providers` |
| `IdentityProviderBootstrap` | Bootstraps providers from config at startup |
| `ExternalOAuthProviderConfigurator` | Configures OIDC/OAuth providers |
| `JdbcIdentityProviderProvisioning` | JDBC implementation executing SQL INSERT |
| `IdentityProviderAliasHandler` | Creates alias IdPs across zones |

---

### 4. Identity Zone Persistence — `IdentityZoneProvisioning.create`

**Key production callers of `create`:**

| Caller | Role |
|---|---|
| `IdentityZoneEndpoints` | REST endpoint: `POST /identity-zones` |
| `JdbcIdentityZoneProvisioning` | JDBC implementation executing SQL INSERT |
| `BootstrapIdentityZones` | Bootstraps zones from config at startup |

---

### 5. Authorization Code Persistence — `JdbcAuthorizationCodeServices`

This class stores authorization codes during the OAuth2 authorization code grant flow. Its `createCode` method is called by:

| Caller | Role |
|---|---|
| `UaaAuthorizationEndpoint` | Generates and persists auth code during `GET /oauth/authorize` |

---

### 6. Client Registration Persistence — `JdbcQueryableClientDetailsService.create`

**Key production callers:**

| Caller | Role |
|---|---|
| `ClientAdminEndpoints` | REST endpoint: `POST /oauth/clients` |
| `ClientAdminBootstrap` | Bootstraps OAuth clients from config |
| `NoOpClientDetailsResourceManager` | No-op variant for testing |

---

## Summary: Data Persistence Entry Points (Production)

| Persistence Domain | Method | HTTP Entry Point | Bootstrap Entry Point |
|---|---|---|---|
| Users | `ScimUserEndpoints.createUser` | `POST /Users` | `ScimUserBootstrap` |
| Users (self-reg) | `EmailAccountCreationService.createUser` | `POST /create_account` | — |
| Users (invite) | `InvitationsEndpoint.createUser` | `POST /invitations/accept` | — |
| Tokens (access) | `UaaTokenServices.createAccessToken` → `persistRevocableToken` | Any OAuth2 grant (`POST /oauth/token`) | — |
| Tokens (refresh) | `DefaultTokenServices.storeRefreshToken` | Any OAuth2 grant | — |
| Identity Providers | `IdentityProviderEndpoints.create` | `POST /identity-providers` | `IdentityProviderBootstrap` |
| Identity Zones | `IdentityZoneEndpoints.create` | `POST /identity-zones` | `BootstrapIdentityZones` |
| Authorization Codes | `UaaAuthorizationEndpoint` → `JdbcAuthorizationCodeServices.createCode` | `GET /oauth/authorize` | — |
| OAuth2 Clients | `ClientAdminEndpoints.create` | `POST /oauth/clients` | `ClientAdminBootstrap` |

---

## Note on `save` vs. UAA's Persistence Pattern

Spring Data JPA uses a `save()` method on repositories. The sample-uaa project does **not** use Spring Data JPA repositories. Instead it uses:
- **JDBC templates directly** (`JdbcTemplate.update(...)`)
- **Custom `Provisioning` interfaces** with `create`, `update`, `upsert` methods
- **JDBC implementations** (e.g., `JdbcScimUserProvisioning`, `JdbcRevocableTokenProvisioning`, `JdbcIdentityProviderProvisioning`)

This is why `claudit graph callers save` returned 0 results — `save` is not part of UAA's persistence vocabulary.
