package org.cloudfoundry.identity.uaa.scim;

import java.util.List;

/**
 * Stub interface — extracted from:
 *   server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupProvisioning.java
 *   server/src/main/java/org/cloudfoundry/identity/uaa/resources/ResourceManager.java
 *   server/src/main/java/org/cloudfoundry/identity/uaa/resources/Queryable.java
 *
 * Only the methods actually called by createGroup() are included:
 *   dao.create(group, zoneId)
 *   dao.delete(id, version, zoneId)
 *
 * The remaining methods (query, retrieve, update, getByName, createOrGet) are stubs
 * because they are not exercised by the createGroup code path.
 */
public interface ScimGroupProvisioning {

    // From ResourceManager<ScimGroup>
    ScimGroup create(ScimGroup resource, String zoneId);
    ScimGroup delete(String id, int version, String zoneId);
    ScimGroup retrieve(String id, String zoneId);
    ScimGroup update(String id, ScimGroup resource, String zoneId);
    List<ScimGroup> retrieveAll(String zoneId);

    // From Queryable<ScimGroup>
    List<ScimGroup> query(String filter, String sortBy, boolean ascending, String zoneId);

    // From ScimGroupProvisioning
    ScimGroup createOrGet(ScimGroup group, String zoneId);
    ScimGroup getByName(String displayName, String zoneId);
}
