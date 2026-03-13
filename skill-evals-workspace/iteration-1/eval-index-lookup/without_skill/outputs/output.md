# ScimGroupProvisioning Definition Lookup

## Commands Run

1. Searched for all files containing `ScimGroupProvisioning` using ripgrep (Grep tool):
   - Pattern: `ScimGroupProvisioning`
   - Path: `/Users/dloffre/proj/claudit/sample-uaa`
   - Mode: `files_with_matches`
   - Found 45 matching files

2. Read the primary definition file:
   - `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupProvisioning.java`

3. Confirmed the definition line with a targeted grep:
   - Pattern: `^(public interface|public class|public abstract class)`
   - Found at line 19

## Result

**File:** `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupProvisioning.java`

**Line:** 19

`ScimGroupProvisioning` is defined as a **Java interface** that extends both `ResourceManager<ScimGroup>` and `Queryable<ScimGroup>`.

## Full Source

```java
/*
 * *****************************************************************************
 *     Cloud Foundry
 *     Copyright (c) [2009-2016] Pivotal Software, Inc. All Rights Reserved.
 *
 *     This product is licensed to you under the Apache License, Version 2.0 (the "License").
 *     You may not use this product except in compliance with the License.
 *
 *     This product includes a number of subcomponents with
 *     separate copyright notices and license terms. Your use of these
 *     subcomponents is subject to the terms and conditions of the
 *     subcomponent's license, as noted in the LICENSE file.
 *******************************************************************************/
package org.cloudfoundry.identity.uaa.scim;

import org.cloudfoundry.identity.uaa.resources.Queryable;
import org.cloudfoundry.identity.uaa.resources.ResourceManager;

public interface ScimGroupProvisioning extends ResourceManager<ScimGroup>, Queryable<ScimGroup> {
    ScimGroup createOrGet(ScimGroup group, String zoneId);

    ScimGroup getByName(String displayName, String zoneId);
}
```

## Notes

The concrete implementation is at:
`/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/jdbc/JdbcScimGroupProvisioning.java`
