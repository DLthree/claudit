# ScimGroupProvisioning — Index Lookup Results

## Commands Run

```bash
claudit index create /Users/dloffre/proj/claudit/sample-uaa
claudit index lookup ScimGroupProvisioning /Users/dloffre/proj/claudit/sample-uaa --kind definitions
claudit index get-body ScimGroupProvisioning /Users/dloffre/proj/claudit/sample-uaa --language java
```

## Index Create Output

```json
{
  "status": "exists",
  "project_dir": "/Users/dloffre/proj/claudit/sample-uaa",
  "gtags_mtime": 1770684652.0193272
}
```

## Lookup Output

```json
{
  "symbol": "ScimGroupProvisioning",
  "definitions": [
    {
      "name": "ScimGroupProvisioning",
      "file": "server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupProvisioning.java",
      "line": 19
    }
  ]
}
```

## File Path and Line Number

**File:** `server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupProvisioning.java`
**Line:** 19

Absolute path: `/Users/dloffre/proj/claudit/sample-uaa/server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupProvisioning.java`

## get-body Output

```json
{
  "function": "ScimGroupProvisioning",
  "file": "server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupProvisioning.java",
  "start_line": 19,
  "end_line": 23,
  "source": "public interface ScimGroupProvisioning extends ResourceManager<ScimGroup>, Queryable<ScimGroup> {\n    ScimGroup createOrGet(ScimGroup group, String zoneId);\n\n    ScimGroup getByName(String displayName, String zoneId);\n}",
  "language": "java"
}
```

## First 30 Lines of Source

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

## Summary

`ScimGroupProvisioning` is a **Java interface** defined at line 19 of `server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupProvisioning.java`. It extends both `ResourceManager<ScimGroup>` and `Queryable<ScimGroup>`, and declares two methods: `createOrGet` and `getByName`. The file is only 23 lines total (the interface body is concise — lines 19–23).
