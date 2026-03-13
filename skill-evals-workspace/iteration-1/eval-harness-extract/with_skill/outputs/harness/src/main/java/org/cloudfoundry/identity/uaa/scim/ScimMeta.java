package org.cloudfoundry.identity.uaa.scim;

import java.util.Date;

// Extracted verbatim from model/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimMeta.java
// Jackson date serializer/deserializer annotations stripped (those classes are deep in uaa-impl).
public class ScimMeta {
    private int version;
    private Date created = new Date();
    private Date lastModified;
    private String[] attributes;

    public ScimMeta() {}

    public ScimMeta(Date created, Date lastModified, int version) {
        this.created = created;
        this.lastModified = lastModified;
        this.version = version;
    }

    public Date getCreated() { return created; }
    public void setCreated(Date created) { this.created = created; }
    public Date getLastModified() { return lastModified; }
    public void setLastModified(Date lastModified) { this.lastModified = lastModified; }
    public void setVersion(int version) { this.version = version; }
    public int getVersion() { return version; }
    public String[] getAttributes() { return attributes; }
    public void setAttributes(String[] attributes) { this.attributes = attributes; }
}
