# Highlighted Source: `createUser` in sample-uaa

## Approach

1. Used `grep` (via the Grep tool) to search all Java files in `/Users/dloffre/proj/claudit/sample-uaa` for occurrences of `createUser`.
2. Identified the interface definition and the primary implementation.
3. Read the relevant source files to extract the function bodies.

## Commands Run

```
Grep pattern="createUser" path=sample-uaa output_mode=files_with_matches
Grep pattern="createUser" path=ScimUserProvisioning.java output_mode=content
Grep pattern="createUser" path=JdbcScimUserProvisioning.java output_mode=content
Read JdbcScimUserProvisioning.java offset=248 limit=65
Read JdbcScimUserProvisioning.java offset=305 limit=15
Read ScimUserProvisioning.java
```

## Findings

### 79 files reference `createUser`

The function appears throughout the codebase in tests, service layers, and integration utilities. The two key locations are:

- **Interface**: `server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimUserProvisioning.java` (line 27)
- **Primary implementation**: `server/src/main/java/org/cloudfoundry/identity/uaa/scim/jdbc/JdbcScimUserProvisioning.java` (lines 311–316)

---

## Interface Declaration

**File**: `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimUserProvisioning.java`

```java
// line 27
ScimUser createUser(ScimUser user, String password, String zoneId) throws InvalidPasswordException, InvalidScimResourceException;
```

---

## Primary Implementation

**File**: `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/jdbc/JdbcScimUserProvisioning.java`

```java
// lines 311–316
@Override
public ScimUser createUser(ScimUser user, final String password, String zoneId) throws InvalidPasswordException,
        InvalidScimResourceException {
    user.setPassword(passwordEncoder.encode(password));
    return create(user, zoneId);
}
```

This is a thin wrapper that:
1. Encodes the provided plain-text password using `passwordEncoder.encode(password)` and sets it on the user object.
2. Delegates all actual persistence work to the `create(user, zoneId)` method.

---

## Delegated Method: `create`

`createUser` immediately calls `create(ScimUser user, String zoneId)` (lines 248–303 in the same file):

```java
// lines 248–303
public ScimUser create(final ScimUser user, String zoneId) {
    UserConfig userConfig = getUserConfig(zoneId);
    validateUserLimit(zoneId, userConfig);
    if (!hasText(user.getOrigin())) {
        user.setOrigin(OriginKeys.UAA);
    }
    if (isCheckOriginEnabled(userConfig)) {
        checkOrigin(user.getOrigin(), zoneId);
    }
    if (logger.isDebugEnabled()) {
        logger.debug("Creating new user: {}", UaaStringUtils.getCleanedUserControlString(user.getUserName()));
    }

    final String id = UUID.randomUUID().toString();
    final String identityZoneId = zoneId;
    final String origin = user.getOrigin();

    try {
        jdbcTemplate.update(CREATE_USER_SQL, ps -> {
            Timestamp t = new Timestamp(new Date().getTime());
            ps.setString(1, id);
            ps.setInt(2, user.getVersion());
            ps.setTimestamp(3, t); // created
            ps.setTimestamp(4, t); // lastModified
            ps.setString(5, user.getUserName());
            ps.setString(6, user.getPrimaryEmail());
            if (user.getName() == null) {
                ps.setString(7, null); // givenName
                ps.setString(8, null); // familyName
            } else {
                ps.setString(7, user.getName().getGivenName());
                ps.setString(8, user.getName().getFamilyName());
            }
            ps.setBoolean(9, user.isActive());
            String phoneNumber = extractPhoneNumber(user);
            ps.setString(10, phoneNumber);
            ps.setBoolean(11, user.isVerified());
            ps.setString(12, origin);
            ps.setString(13, hasText(user.getExternalId()) ? user.getExternalId() : null);
            ps.setString(14, identityZoneId);
            ps.setString(15, hasText(user.getAliasId()) ? user.getAliasId() : null);
            ps.setString(16, hasText(user.getAliasZid()) ? user.getAliasZid() : null);
            ps.setString(17, user.getSalt());
            ps.setTimestamp(18, getPasswordLastModifiedTimestamp(t));
            ps.setNull(19, Types.BIGINT); // last_logon_success_time
            ps.setNull(20, Types.BIGINT); // previous_logon_success_time
            ps.setString(21, user.getPassword());
        });
    } catch (DuplicateKeyException e) {
        String userOrigin = hasText(user.getOrigin()) ? user.getOrigin() : OriginKeys.UAA;
        Map<String, Object> userDetails = Collections.singletonMap("origin", userOrigin);
        throw new ScimResourceAlreadyExistsException("Username already in use: " + user.getUserName(), userDetails);
    }
    return retrieve(id, zoneId);
}
```

### What `create` does (step by step)

| Step | Description |
|------|-------------|
| 1 | Retrieves zone-specific `UserConfig` and validates the user count limit |
| 2 | Defaults the origin to `"uaa"` if not set |
| 3 | Optionally checks that the origin is allowed in the zone |
| 4 | Generates a random UUID as the new user's `id` |
| 5 | Executes `CREATE_USER_SQL` (a prepared statement) with 21 bound parameters covering all SCIM user fields |
| 6 | Catches `DuplicateKeyException` and re-throws as `ScimResourceAlreadyExistsException` with the username |
| 7 | Returns the newly persisted user by calling `retrieve(id, zoneId)` |
