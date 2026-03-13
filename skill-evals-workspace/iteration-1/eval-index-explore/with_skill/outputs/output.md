# Index Exploration: sample-uaa

## Task
Explore the Java project at `/Users/dloffre/proj/claudit/sample-uaa` using the `claudit index` skill before a security audit.

---

## Commands Run and Output

### 1. Create the Index

```bash
claudit index create /Users/dloffre/proj/claudit/sample-uaa
```

**Output:**
```json
{
  "status": "exists",
  "project_dir": "/Users/dloffre/proj/claudit/sample-uaa",
  "gtags_mtime": 1770684652.0193272
}
```

The index already existed (was previously built). Status `"exists"` confirms the GNU Global index (GTAGS/GRTAGS/GPATH files) is present at the project root.

---

### 2. List Symbols

```bash
claudit index list-symbols /Users/dloffre/proj/claudit/sample-uaa
```

**Total symbols:** 12,062

**First 50 symbols (alphabetical):**

```
A
AbstractClientAdminEvent
AbstractClientParametersAuthenticationFilter
AbstractDefaultTokenServicesTests
AbstractEndpoint
AbstractExceptionTestSupport
AbstractExternalOAuthIdentityProviderDefinition
AbstractIdentityProviderDefinition
AbstractLdapMockMvcTest
AbstractOAuth2AccessTokenMatchers
AbstractOAuth2SecurityExceptionHandler
AbstractPasswordChangeEvent
AbstractPersistentDefaultTokenServicesTests
AbstractQueryable
AbstractRedirectResourceDetails
AbstractTokenGranter
AbstractTokenMockMvcTests
AbstractUaaAuthenticationEvent
AbstractUaaEvent
AbstractUaaEventTest
AbstractUaaPrincipalEvent
AcceptedInvitation
AccessController
AccessControllerTests
AccessTokenConverter
AccessTokenErrorHandler
AccessTokenProvider
AccessTokenProviderChain
AccessTokenProviderChainTests
AccessTokenRequest
AccessTokenRequiredException
AccessTokenValidation
AccountCreationResponse
AccountCreationService
AccountLoginPolicy
AccountNotPreCreatedException
AccountNotVerifiedException
AccountSavingAuthenticationSuccessHandler
AccountSavingAuthenticationSuccessHandlerTest
AccountsController
AccountsControllerMockMvcTests
AccountsControllerTest
ActionResult
AdminClientCreator
AfterFilter
AfterSeedCallback
Alias
AliasEntitiesConfig
AliasEntitiesDisabled
AliasEntitiesEnabled
```

---

### 3. Lookup Example: AuthzAuthenticationManager

```bash
claudit index lookup AuthzAuthenticationManager /Users/dloffre/proj/claudit/sample-uaa --kind definitions
```

**Output:**
```json
{
  "symbol": "AuthzAuthenticationManager",
  "definitions": [
    {
      "name": "AuthzAuthenticationManager",
      "file": "server/src/main/java/org/cloudfoundry/identity/uaa/authentication/manager/AuthzAuthenticationManager.java",
      "line": 42
    }
  ]
}
```

### 4. Lookup Example: UaaTokenServices

```bash
claudit index lookup UaaTokenServices /Users/dloffre/proj/claudit/sample-uaa --kind definitions
```

**Output:**
```json
{
  "symbol": "UaaTokenServices",
  "definitions": [
    {
      "name": "UaaTokenServices",
      "file": "server/src/main/java/org/cloudfoundry/identity/uaa/oauth/UaaTokenServices.java",
      "line": 128
    }
  ]
}
```

---

## Codebase Structure Interpretation

### Project Overview

`sample-uaa` is the **Cloud Foundry UAA (User Account and Authentication)** server — a large, production-grade OAuth2/OpenID Connect authorization server written in Java using Spring Framework.

### Module Layout

The project is a Gradle multi-module build with these key modules:

| Module | Purpose |
|--------|---------|
| `server/` | Core UAA server logic (authentication, OAuth2, SCIM, SAML, LDAP) |
| `uaa/` | Spring Boot application entry point and web configuration |
| `model/` | Shared domain model classes |
| `statsd-lib/` | StatsD metrics integration |

### Key Functional Areas (from symbol analysis)

**Authentication & Authorization**
- `AuthzAuthenticationManager` — core username/password authentication
- `AbstractClientParametersAuthenticationFilter` — OAuth2 client credential filtering
- `BackwardsCompatibleTokenEndpointAuthenticationFilter` — token endpoint auth
- `AutologinAuthenticationManager` / `AutologinRequestConverter` — auto-login flows
- `ChainedAuthenticationManager` — chained authentication strategies
- `CachingPasswordEncoder` / `BackwardsCompatibleDelegatingPasswordEncoder` — password hashing

**OAuth2 / Token Services**
- `UaaTokenServices` — central token creation and validation (line 128 of oauth module)
- `AbstractTokenGranter` / `AuthorizationCodeTokenGranter` — OAuth2 grant types
- `AccessTokenConverter` / `AccessTokenValidation` — token introspection/conversion
- `AuthorizationCodeServices` / `AuthorizationCodeAccessTokenProvider` — auth code flow
- `AuthorizationServer` / `AuthorizationServerBeanConfiguration` — server config
- `BearerTokenExtractor` — bearer token parsing from requests

**SCIM (User/Group Management)**
- Large set of SCIM-prefixed symbols (ScimUser, ScimGroup, ScimUserProvisioning, etc.)
- `AccountCreationService` / `AccountsController` — user account lifecycle
- `AdminClientCreator` — admin bootstrapping

**Identity Providers**
- `AbstractIdentityProviderDefinition` / `AbstractExternalOAuthIdentityProviderDefinition` — IdP abstraction
- SAML: `BootstrapSamlIdentityProviderData`, `BaseSamlKeyManagerImpl`, `BaseUaaRelyingPartyRegistrationRepository`
- LDAP: `AbstractLdapMockMvcTest`, `BaseLdapSocketFactory`

**Audit & Events**
- `AbstractUaaEvent` / `AbstractUaaAuthenticationEvent` / `AbstractUaaPrincipalEvent` — event hierarchy
- `AuditEvent` / `AuditListener` / `AuditEventType` — comprehensive audit trail
- `ApprovalModifiedEvent` — OAuth2 approval change auditing

**Multi-tenancy / Zones**
- `AliasEntitiesConfig` / `AliasFeatureEnabled` / `AliasMockMvcTestBase` — identity zone aliasing
- Zone-scoped resources throughout

**Security Infrastructure**
- `AnyOfAuthorizationManager` / `AuthorizationManagersUtils` — authorization decisions
- `AccountLoginPolicy` — login policy enforcement
- `AuthorizationAttributesParser` — scope/authority parsing
- `ApprovalsAdminEndpoints` / `ApprovalsSecurityConfiguration` — consent management

**Rate Limiting**
- `BucketRingBoundsException` — likely bucket-based rate limiting (visible in `ratelimiting/` package)

### Scale
With **12,062 symbols** across classes, interfaces, methods, fields, and test types, this is a large enterprise codebase. The high proportion of `*Test`, `*IT` (integration test), and `*MockMvcTests` symbols indicates strong test coverage. Security-relevant classes are concentrated in `server/src/main/java/org/cloudfoundry/identity/uaa/` under packages: `authentication/`, `oauth/`, `scim/`, `provider/`, `audit/`, and `security/`.

---

## Security Audit Starting Points

Based on the index, high-priority areas for a security audit include:

1. **`UaaTokenServices`** — token signing, validation, and claims handling
2. **`AuthzAuthenticationManager`** — credential validation logic
3. **`AuthorizationCodeServices`** — authorization code storage and expiry
4. **`BearerTokenExtractor`** — token extraction from HTTP requests (header/param handling)
5. **`CachingPasswordEncoder` / `BackwardsCompatibleDelegatingPasswordEncoder`** — password security
6. **SAML/LDAP providers** — external IdP trust boundaries
7. **`ApprovalsAdminEndpoints`** — admin-level consent management
8. **`AccountLoginPolicy`** — brute-force/lockout enforcement
