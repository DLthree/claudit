# Java Project Exploration: sample-uaa Security Audit Preparation

## Approach

Explored the `sample-uaa` project at `/Users/dloffre/proj/claudit/sample-uaa` using a combination of:
- Directory listing commands (`ls`)
- `find` with `xargs grep` to extract type declarations, method signatures, and annotations
- GNU Global (`global`) for detailed symbol lookup in key files
- Package and annotation scanning to understand architecture

---

## Commands Run

### Project Structure
```
ls /Users/dloffre/proj/claudit/sample-uaa/
ls /Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/
ls /Users/dloffre/proj/claudit/sample-uaa/model/src/main/java/org/cloudfoundry/identity/uaa/
cat /Users/dloffre/proj/claudit/sample-uaa/settings.gradle
```

### Java Symbol Extraction
```
find .../sample-uaa -name "*.java" | wc -l
find .../sample-uaa -name "*.java" -path "*/main/*" | xargs grep -h "^public class..." | sort -u
find .../sample-uaa -name "*.java" -path "*/main/*" | xargs grep -h "^public interface " | sort -u
find .../sample-uaa -name "*.java" -path "*/main/*" | xargs grep -h "^public enum " | sort -u
find .../sample-uaa -name "*.java" -path "*/main/*" | xargs grep -h "^public abstract class " | sort -u
find .../sample-uaa -name "*.java" -path "*/main/*" | xargs grep -lh "@RestController|@Controller" | sort
find .../sample-uaa -name "*.java" -path "*/main/*" | xargs grep -h "@RequestMapping|@GetMapping|@PostMapping..." | sort -u
find .../sample-uaa -name "*.java" -path "*/main/*" | xargs grep -h "    public " | grep "(" | sort -u | wc -l
find .../sample-uaa -name "*.java" -path "*/main/*" | xargs grep -h "^package " | sort -u
```

### GNU Global for Detailed Method Listings
```
global -f server/src/main/java/org/cloudfoundry/identity/uaa/oauth/UaaAuthorizationEndpoint.java
global -f server/src/main/java/org/cloudfoundry/identity/uaa/oauth/UaaTokenServices.java
global -f server/src/main/java/org/cloudfoundry/identity/uaa/scim/endpoints/ScimUserEndpoints.java
global -f server/src/main/java/org/cloudfoundry/identity/uaa/client/ClientAdminEndpoints.java
```

---

## Key Metrics

| Metric | Count |
|---|---|
| Total Java files | 1,741 |
| Total top-level type declarations (classes, interfaces, enums) | 895 |
| Public classes | 709 |
| Public interfaces | ~100 |
| Public enums | 10 |
| Public abstract classes | ~30 |
| REST/MVC controllers | 40 |
| Security filter classes | 42 |
| @Configuration classes | 79 |
| Manager/Service/Provider/Handler/Filter/Endpoint/Controller classes | 210 |
| Distinct Java packages | 108 |
| Public method declarations | ~4,022 |

---

## Project Module Structure (settings.gradle)

The project is a Gradle multi-module build named `cloudfoundry-identity-parent`:

| Module | Directory |
|---|---|
| `cloudfoundry-identity-model` | `model/` |
| `cloudfoundry-identity-server` | `server/` |
| `cloudfoundry-identity-uaa` | `uaa/` |
| `cloudfoundry-identity-metrics-data` | `metrics-data/` |
| `cloudfoundry-identity-statsd` | `statsd/` |
| `cloudfoundry-identity-statsd-lib` | `statsd-lib/` |

---

## Package Hierarchy

The main application code lives in `org.cloudfoundry.identity.uaa.*` with the following top-level packages:

- **account** - User account management, password, email changes, profile
- **alias** - Entity aliasing support across zones
- **approval** - OAuth2 scope approval management
- **audit** - Audit event logging
- **authentication** - Authentication filters, managers, and events
- **authorization** - Authorization utilities
- **brave** - Distributed tracing (Brave/Zipkin integration)
- **cache** - Caching utilities
- **client** - OAuth2 client management
- **codestore** - One-time code storage (for verification links, etc.)
- **constants** - Shared constants
- **db** - Database migrations (HSQLDB, MySQL, PostgreSQL)
- **error** - Error handling
- **health** - Health check endpoint
- **home** - Home page controller
- **impl** - Configuration implementations
- **invitations** - User invitation flow
- **login** - Login UI and flows
- **logout** - Logout handling
- **message** - Email/messaging service
- **metrics** - StatsD/JMX metrics
- **oauth** - OAuth2/OIDC core (JWT, token services, endpoints, PKCE, JWK)
- **passcode** - One-time passcode authentication
- **provider** - Identity providers (LDAP, SAML, external OAuth/OIDC)
- **ratelimiting** - Rate limiting framework
- **resources** - JDBC query/resource management
- **saml** - SAML protocol support
- **scim** - SCIM 2.0 user and group provisioning
- **security** - Security configuration, CORS, CSP
- **user** - UAA user model
- **util** - Utility classes
- **web** - Web filter chain, request handling
- **zone** - Multi-tenancy (identity zones)

---

## REST API Endpoints (Controllers)

### OAuth2 / OIDC
- `UaaAuthorizationEndpoint` - `/oauth/authorize` (GET, POST) - authorization code + implicit flows
- `UaaTokenEndpoint` / `TokenEndpoint` - `/oauth/token` (GET, POST)
- `CheckTokenEndpoint` - `/check_token` (POST)
- `TokenKeyEndpoint` - `/token_key`, `/token_keys` (GET)
- `IntrospectEndpoint` - token introspection
- `TokenRevocationEndpoint` - `/oauth/token/revoke/{tokenId}` (DELETE), `/oauth/token/list` (GET/DELETE)
- `AccessController` - `/oauth/confirm_access` (GET, POST)

### SCIM User Management
- `ScimUserEndpoints` - `/Users` (GET/POST), `/Users/{userId}` (GET/PUT/PATCH/DELETE), verify, verify-link, status
- `ScimGroupEndpoints` - `/Groups`, `/Groups/{groupId}`, `/Groups/External`, membership management
- `ChangeEmailEndpoints` - email change workflow
- `UserIdConversionEndpoints` - ID ↔ username conversion

### Client Management
- `ClientAdminEndpoints` - `/oauth/clients` CRUD, secret changes, JWT credential changes
- `ClientMetadataAdminEndpoints` - `/oauth/clients/{client}/meta`
- `ClientInfoEndpoint` - `/clientinfo`

### Account / Profile
- `AccountsController` - `/create_account`, `/email_sent`
- `ProfileController` - `/profile`
- `PasswordChangeEndpoint` - `/password_change`
- `PasswordResetEndpoint` - `/password_reset`
- `ResetPasswordController` - `/forgot_password`, `/reset_password`
- `ChangePasswordController` - `/change_password`
- `ChangeEmailController` - `/change_email`
- `UserInfoEndpoint` - user info (OIDC userinfo endpoint)
- `OpenIdConnectEndpoints` - OIDC discovery

### Identity Providers / Zones
- `IdentityProviderEndpoints` - `/identity-providers` CRUD
- `IdentityZoneEndpoints` - `/identity-zones` CRUD
- `SamlMetadataEndpoint` - `/saml/metadata`

### Other
- `ApprovalsAdminEndpoints` - `/approvals`
- `PasscodeEndpoint` - `/passcode`
- `CodeStoreEndpoints` - `/Codes/{code}`
- `HealthzEndpoint` - `/healthz`
- `RateLimitStatusController` - rate limit status
- `LoginInfoEndpoint` - `/login`
- `HomeController` - `/`
- `InvitationsController`, `InvitationsEndpoint` - invitation flows
- `SessionController`, `LoggedOutEndpoint` - session/logout

---

## Key Token Granter Implementations

The following OAuth2 grant types are implemented:

| Class | Grant Type |
|---|---|
| `AuthorizationCodeTokenGranter` | authorization_code |
| `PkceEnhancedAuthorizationCodeTokenGranter` | authorization_code with PKCE |
| `ResourceOwnerPasswordTokenGranter` | password |
| `ImplicitTokenGranter` | implicit |
| `RefreshTokenGranter` | refresh_token |
| `ClientCredentialsTokenGranter` | client_credentials |
| `HybridTokenGranterForAuthorizationCode` | hybrid (code + token) |
| `JwtTokenGranter` | JWT bearer assertion |
| `Saml2TokenGranter` | SAML2 bearer assertion |
| `TokenExchangeGranter` | token exchange (RFC 8693) |
| `UserTokenGranter` | user-to-user token |
| `IdTokenGranter` | OIDC id_token |
| `CompositeTokenGranter` | delegates to all the above |

---

## Authentication Manager Implementations

| Class | Purpose |
|---|---|
| `AuthzAuthenticationManager` | Internal UAA username/password auth |
| `DynamicZoneAwareAuthenticationManager` | Zone-aware auth dispatch |
| `ChainedAuthenticationManager` | Chains multiple managers |
| `CompositeAuthenticationManager` | Composite of managers |
| `LdapLoginAuthenticationManager` | LDAP authentication |
| `DynamicLdapAuthenticationManager` | Dynamic LDAP auth |
| `ExternalLoginAuthenticationManager` | Base for external IdP auth |
| `ExternalOAuthAuthenticationManager` | External OAuth/OIDC |
| `LoginAuthenticationManager` | Login server auth |
| `AutologinAuthenticationManager` | Autologin token auth |
| `OAuth2AuthenticationManager` | OAuth2 resource server auth |
| `PasswordGrantAuthenticationManager` | Password grant |
| `ScopeAuthenticationManager` | Scope-based authorization |
| `CheckIdpEnabledAuthenticationManager` | IdP enabled check |
| `UsernamePasswordExtractingAuthenticationManager` | Credential extraction |
| `RestAuthenticationManager` | REST-based (remote) auth |

---

## Security Filters (Filter Chain)

Key filters in the security pipeline:

- `AuthzAuthenticationFilter` - username/password extraction
- `ClientBasicAuthenticationFilter` - HTTP Basic client auth
- `ClientParametersAuthenticationFilter` / `LoginClientParametersAuthenticationFilter` - client credential params
- `BackwardsCompatibleTokenEndpointAuthenticationFilter` - token endpoint auth
- `OAuth2AuthenticationProcessingFilter` - Bearer token processing
- `PasscodeAuthenticationFilter` - passcode authentication
- `SessionResetFilter` - session invalidation
- `PasswordChangeRequiredFilter` / `PasswordChangeUiRequiredFilter` - force password change
- `ReAuthenticationRequiredFilter` - step-up auth
- `CurrentUserCookieRequestFilter` - current user cookie management
- `IdentityZoneResolvingFilter` - multi-tenant zone resolution
- `IdentityZoneSwitchingFilter` - zone switching for admin
- `ExternalOAuthAuthenticationFilter` - external OAuth callback
- `RateLimitingFilter` - rate limiting enforcement
- `LimitedModeUaaFilter` - limited operation mode
- `DisableIdTokenResponseTypeFilter` - id_token response type control
- `CorsFilter` - CORS policy enforcement
- `ContentSecurityPolicyFilter` - CSP headers
- `HttpsHeaderFilter` - HTTPS headers
- `UaaMetricsFilter` - request metrics
- `BackwardsCompatibleScopeParsingFilter` - legacy scope parsing
- `DisableUserManagementSecurityFilter` / `DisableInternalUserManagementFilter` - user mgmt controls

---

## Core Interfaces (Security Audit Relevance)

| Interface | Purpose |
|---|---|
| `TokenStore` | Token persistence |
| `AuthorizationCodeServices` | Auth code storage |
| `RevocableTokenProvisioning` | Token revocation |
| `PasswordValidator` | Password policy enforcement |
| `PkceVerifier` | PKCE code verifier |
| `RedirectResolver` | OAuth2 redirect URI validation |
| `ApprovalStore` | Scope approval persistence |
| `ExpiringCodeStore` | One-time code storage |
| `IdentityProviderProvisioning` | IdP configuration storage |
| `IdentityZoneProvisioning` | Zone configuration storage |
| `ScimUserProvisioning` | User account provisioning |
| `ScimGroupProvisioning` | Group provisioning |
| `UaaAuditService` | Audit event persistence |
| `LockoutPolicyRetriever` | Account lockout configuration |
| `LoginPolicy` / `AccountLoginPolicy` | Login attempt policy |
| `ClientDetailsService` / `ClientDetailsValidator` | Client validation |
| `RateLimiter` / `LimiterManager` | Rate limiting |
| `Jwt` / `Signer` / `Verifier` | JWT operations |
| `SamlKeyManager` | SAML key management |

---

## Data Model (SCIM / Core Types)

- `ScimUser` - SCIM 2.0 user entity (implements `EntityWithAlias`)
- `ScimGroup` - SCIM 2.0 group entity
- `ScimGroupMember` - Group membership
- `ScimGroupExternalMember` - External group mapping
- `Approval` - OAuth2 scope approval record
- `UaaUser` - Internal UAA user model
- `UaaPrincipal` - Security principal (also `UaaSamlPrincipal`)
- `RevocableToken` - Token revocation record
- `AuditEvent` - Audit log record
- `IdentityProvider` / `IdentityZone` - Multi-tenancy models

---

## Audit Event Types (`AuditEventType` enum)

Stored in the database by numeric code (do not change):

| Code | Event |
|---|---|
| 0 | UserAuthenticationSuccess |
| 1 | UserAuthenticationFailure |
| 2 | UserNotFound |
| 3 | PasswordChangeSuccess |
| 4 | PrincipalAuthenticationSuccess |
| 5 | PrincipalAuthenticationFailure |
| 8 | SecretChangeSuccess |
| 9 | SecretChangeFailure |
| 10-12 | Client Create/Update/Delete Success |
| 14-15 | ClientAuthenticationSuccess/Failure |
| 16 | ApprovalModifiedEvent |
| 17 | TokenIssuedEvent |
| 18-20 | UserCreated/Modified/Deleted |
| 21 | UserVerifiedEvent |
| 22 | PasswordResetRequest |
| 23-25 | Group Created/Modified/Deleted |
| 28-29 | IdentityProviderCreated/Modified |
| 30-31 | IdentityZoneCreated/Modified |
| 36 | TokenRevocationEvent |
| 37-38 | IdentityProviderAuthenticationSuccess/Failure |
| 41-42 | ClientJwtChangeSuccess/Failure |

---

## Exception Hierarchy (Security-Relevant)

- `UaaException extends OAuth2Exception` - base UAA exception
- `InvalidTokenException` - invalid/expired tokens
- `TokenRevokedException extends InvalidTokenException`
- `InvalidClientException` - bad client credentials
- `InvalidGrantException` - invalid grant type or code
- `InvalidScopeException` - scope not allowed
- `InvalidClientDetailsException` - client config errors
- `RedirectMismatchException` - redirect URI mismatch (open redirect protection)
- `PkceValidationException` - PKCE verification failure
- `AuthenticationPolicyRejectionException` - lockout/policy rejection
- `InternalUserManagementDisabledException` - user mgmt disabled
- `DisallowedIdpException` - IdP not permitted for client
- `InteractionRequiredException` - requires user interaction
- `PasswordChangeRequiredException` - forced password change

---

## Identity Provider Support

### Internal
- `AuthzAuthenticationManager` - UAA internal user store

### LDAP
- `LdapLoginAuthenticationManager` - LDAP auth
- `LdapIdentityProviderDefinition` - LDAP configuration
- `DefaultLdapAuthoritiesPopulator`, `NestedLdapAuthoritiesPopulator` - group mapping
- `LdapGroupToScopesMapper` - LDAP groups to OAuth scopes
- `PasswordComparisonAuthenticator` - LDAP password comparison mode
- `SpringSecurityLdapTemplate` - LDAP operations
- TLS support: `LdapSocketFactory`, `SkipSslLdapSocketFactory`, `BaseLdapSocketFactory`

### SAML
- `SamlIdentityProviderDefinition`, `SamlIdentityProviderConfigurator`
- `SamlUaaResponseAuthenticationConverter`, `SamlUaaAuthenticationUserManager`
- `SamlLogoutRequestValidator`, `SamlLogoutResponseValidator`
- `BootstrapSamlIdentityProviderData` - SAML IdP bootstrapping
- `ZoneAwareKeyManager` - zone-aware SAML key management

### External OAuth / OIDC
- `OIDCIdentityProviderDefinition`, `RawExternalOAuthIdentityProviderDefinition`
- `ExternalOAuthAuthenticationManager`, `ExternalOAuthAuthenticationFilter`
- `ExternalOAuthProviderConfigurator` - implements `IdentityProviderProvisioning`

---

## Cryptographic / JWT Components

- `JwtHelper`, `JwtImpl`, `JwtAlgorithms` - JWT construction and parsing
- `KeyInfo`, `KeyInfoService`, `KeyInfoBuilder` - signing key management
- `KeyWithCert` - certificate-backed key
- `UaaMacSigner` - HMAC signing
- `SignatureVerifier`, `ChainedSignatureVerifier` - JWT signature verification
- `JsonWebKey`, `JsonWebKeySet`, `VerificationKeyResponse` - JWK(S) support
- `S256PkceVerifier` - PKCE SHA-256 verifier
- `CachingPasswordEncoder` - BCrypt with caching
- `BackwardsCompatibleDelegatingPasswordEncoder` - multi-algorithm password encoding
- `DynamicPasswordComparator` - dynamic algorithm comparison
- `AlphanumericRandomValueStringGenerator`, `UaaRandomStringUtilImpl` - secure random generation

---

## Database Layer (JDBC Provisioning)

| Class | Entity |
|---|---|
| `JdbcScimUserProvisioning` | Users |
| `JdbcScimGroupProvisioning` | Groups |
| `JdbcScimGroupMembershipManager` | Group memberships |
| `JdbcScimGroupExternalMembershipManager` | External group mappings |
| `JdbcUaaUserDatabase` | UAA user lookups |
| `MultitenantJdbcClientDetailsService` | OAuth2 clients |
| `JdbcClientMetadataProvisioning` | Client metadata |
| `JdbcIdentityProviderProvisioning` | Identity providers |
| `JdbcIdentityZoneProvisioning` | Identity zones |
| `JdbcApprovalStore` | Scope approvals |
| `JdbcRevocableTokenProvisioning` | Revocable tokens |
| `JdbcAuditService` / `JdbcUnsuccessfulLoginCountingAuditService` | Audit logs |
| `JdbcExpiringCodeStore` | One-time codes |
| `JdbcAuthorizationCodeServices` | Authorization codes |

Supports MySQL, PostgreSQL, and HSQLDB with Flyway migrations.

---

## Rate Limiting

Standalone rate limiting framework in `org.cloudfoundry.identity.uaa.ratelimiting.*`:

- `RateLimitingFilter` - main servlet filter
- `RateLimiter` interface + `LimiterManager` / `InternalLimiterFactory`
- `RateLimitStatusController` - status endpoint
- `LimiterByCompoundKey`, `ExpirationBuckets` - key-based limiting
- `RateLimitingConfigMapper` - YAML configuration loading

---

## Multi-Tenancy (Identity Zones)

- `IdentityZoneResolvingFilter` - resolves zone from hostname/path
- `IdentityZoneSwitchingFilter` - admin zone switching
- `IdentityZoneManager` interface / `IdentityZoneProvisioning`
- `ZoneAware` interface - zone context awareness
- `ZoneAwareKeyManager`, `ZoneAwareWhitelistLogoutSuccessHandler`
- `ZoneAwareClientSecretPolicyValidator`
- `DelegatingRelyingPartyRegistrationRepository` - zone-aware SAML registration

---

## Interpretation / Security Audit Notes

### Attack Surface
The UAA is a large, feature-rich OAuth2/OIDC Authorization Server. The primary attack surface includes:

1. **Token issuance endpoints** (`/oauth/token`, `/oauth/authorize`) - high-value targets for token manipulation, bypass, or forging.
2. **Redirect URI validation** (`RedirectMismatchException`, `UaaAuthorizationEndpoint.buildRedirectURI`) - open redirect risk if validation is weak.
3. **PKCE implementation** (`PkceEnhancedAuthorizationCodeTokenGranter`, `S256PkceVerifier`) - authorization code interception prevention.
4. **JWT signing/verification** (`KeyInfo`, `ChainedSignatureVerifier`, `JwtAlgorithms`) - algorithm confusion attacks (e.g., RS256 → HS256 downgrade).
5. **Password encoding** (`BackwardsCompatibleDelegatingPasswordEncoder`, `CachingPasswordEncoder`) - legacy algorithm support may be a risk.
6. **LDAP integration** (`SpringSecurityLdapTemplate`, `SkipSslLdapSocketFactory`) - LDAP injection, SSL bypass in non-production configs.
7. **SAML integration** - XML signature wrapping, metadata spoofing via `SamlLogoutRequestValidator` / `SamlLogoutResponseValidator`.
8. **External OAuth/OIDC** (`ExternalOAuthAuthenticationManager`) - token validation, issuer verification.
9. **Multi-tenancy** - zone isolation, cross-zone data leakage via `IdentityZoneResolvingFilter`.
10. **Rate limiting** - effectiveness and bypass potential.
11. **Audit logging** (`AuditEventType`, `JdbcAuditService`) - completeness and tamper-resistance.
12. **One-time codes** (`JdbcExpiringCodeStore`) - predictability, timing attacks.
13. **CORS policy** (`CorsFilter`) - misconfiguration risk.
14. **Content Security Policy** (`ContentSecurityPolicyFilter`) - XSS mitigation.
15. **Session management** (`SessionResetFilter`, `UaaSavedRequestCache`) - session fixation.

### Notable Design Patterns
- Event-driven audit trail via Spring `ApplicationEvent` / `ApplicationEventPublisher`
- Zone-aware everything - most services implement `ZoneAware` or accept zone context
- JDBC-backed storage for all security-sensitive data (tokens, codes, approvals)
- Backwards compatibility maintained via delegating encoders and filters
- Extensive filter chain for defense-in-depth
