package org.cloudfoundry.identity.uaa.scim;

// Extracted verbatim from model/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimCore.java
// Assert replaced with inline check to remove spring-core dependency on this class.
public abstract class ScimCore<T extends ScimCore> {

    public static final String[] SCHEMAS = new String[]{"urn:scim:schemas:core:1.0"};

    private String id;
    private String externalId;
    private ScimMeta meta = new ScimMeta();

    protected ScimCore(String id) { this.id = id; }
    protected ScimCore() {}

    public void setSchemas(String[] schemas) {}

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getExternalId() { return externalId; }
    public ScimCore setExternalId(String externalId) { this.externalId = externalId; return this; }

    public ScimMeta getMeta() { return meta; }
    public void setMeta(ScimMeta meta) { this.meta = meta; }

    public void setVersion(int version) { meta.setVersion(version); }
    public int getVersion() { return meta.getVersion(); }

    public String[] getSchemas() { return SCHEMAS; }

    public void patch(T patch) {}

    @Override
    public int hashCode() { return id != null ? id.hashCode() : super.hashCode(); }

    @Override
    public boolean equals(Object o) {
        if (o instanceof ScimCore other) {
            return id != null && id.equals(other.id);
        } else if (o instanceof String otherId) {
            return id != null && id.equals(otherId);
        }
        return false;
    }
}
