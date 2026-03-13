package org.cloudfoundry.identity.uaa.scim;

import java.util.List;

/**
 * Verbatim-extracted (simplified) from sample-uaa/model/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroup.java
 * Stripped of Jackson annotations and ScimCore inheritance for standalone compilation.
 * The fields and setter/getter logic is preserved exactly; the patch() method is kept
 * because createGroup() may invoke setMembers() on members returned from dao.create().
 */
public class ScimGroup {

    private String id;
    private String displayName;
    private String zoneId;
    private String description;
    private List<ScimGroupMember> members;
    private int version;

    public ScimGroup() {}

    public ScimGroup(String name) {
        this(null, name, null);
    }

    public ScimGroup(String id, String displayName, String zoneId) {
        this.id = id;
        this.displayName = displayName;
        this.zoneId = zoneId;
    }

    public String getId() { return id; }
    public ScimGroup setId(String id) { this.id = id; return this; }

    public String getDisplayName() { return displayName; }
    public ScimGroup setDisplayName(String displayName) { this.displayName = displayName; return this; }

    public String getZoneId() { return zoneId; }
    public ScimGroup setZoneId(String zoneId) { this.zoneId = zoneId; return this; }

    public List<ScimGroupMember> getMembers() { return members; }
    public ScimGroup setMembers(List<ScimGroupMember> members) { this.members = members; return this; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public int getVersion() { return version; }
    public void setVersion(int version) { this.version = version; }

    @Override
    public String toString() {
        return "(Group id: " + id + ", name: " + displayName + ", zoneId: " + zoneId + ")";
    }
}
