package org.cloudfoundry.identity.uaa.scim;

/**
 * Extracted from sample-uaa/model/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupMember.java
 * Stripped of Jackson annotations and ScimCore generic type for standalone compilation.
 */
public class ScimGroupMember {

    public enum Type {
        USER, GROUP
    }

    private String memberId;
    private String origin = "uaa";
    private String operation;
    private Type type;

    public ScimGroupMember() {}

    public ScimGroupMember(String memberId) {
        this(memberId, Type.USER);
    }

    public ScimGroupMember(String memberId, Type type) {
        this.memberId = memberId;
        this.type = type;
    }

    public String getMemberId() { return memberId; }
    public void setMemberId(String memberId) { this.memberId = memberId; }

    public Type getType() { return type; }
    public void setType(Type type) { this.type = type; }

    public String getOrigin() { return origin; }
    public void setOrigin(String origin) {
        if (origin == null) throw new NullPointerException();
        this.origin = origin;
    }

    public String getOperation() { return operation; }
    public void setOperation(String operation) { this.operation = operation; }

    @Override
    public String toString() {
        return "(memberId: " + memberId + ", type: " + type + ", origin: " + origin + ")";
    }
}
