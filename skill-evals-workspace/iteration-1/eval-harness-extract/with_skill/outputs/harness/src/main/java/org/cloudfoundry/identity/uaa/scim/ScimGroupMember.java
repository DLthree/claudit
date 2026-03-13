package org.cloudfoundry.identity.uaa.scim;

// Extracted verbatim from model/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupMember.java
// OriginKeys.UAA constant inlined; Jackson annotations kept for JSON serialization tests.
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class ScimGroupMember<TEntity extends ScimCore> {

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public enum Type { USER, GROUP }

    @JsonProperty("value")
    private String memberId;
    private String origin = "uaa"; // OriginKeys.UAA inlined
    private String operation;
    private Type type;
    private TEntity entity;

    public ScimGroupMember() {}
    public ScimGroupMember(String memberId) { this(memberId, Type.USER); }
    public ScimGroupMember(TEntity entity) { this(entity.getId(), getEntityType(entity)); setEntity(entity); }
    public ScimGroupMember(String memberId, Type type) { this.memberId = memberId; this.type = type; }

    public TEntity getEntity() { return entity; }
    public void setEntity(TEntity entity) { this.entity = entity; }
    public String getMemberId() { return memberId; }
    public void setMemberId(String memberId) { this.memberId = memberId; }
    public Type getType() { return type; }
    public void setType(Type type) { this.type = type; }
    public String getOperation() { return operation; }
    public void setOperation(String operation) { this.operation = operation; }
    public String getOrigin() { return origin; }
    public void setOrigin(String origin) {
        if (origin == null) throw new NullPointerException();
        this.origin = origin;
    }

    @Override
    public String toString() {
        return "(memberId: %s, type: %s, origin:%s)".formatted(getMemberId(), getType(), getOrigin());
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ScimGroupMember member = (ScimGroupMember) o;
        if (getMemberId() != null ? !getMemberId().equals(member.getMemberId()) : member.getMemberId() != null) return false;
        return getType() == member.getType();
    }

    @Override
    public int hashCode() {
        int result = getMemberId() != null ? getMemberId().hashCode() : 0;
        result = 31 * result + (getOrigin() != null ? getOrigin().hashCode() : 0);
        result = 31 * result + (getType() != null ? getType().hashCode() : 0);
        return result;
    }

    private static Type getEntityType(ScimCore entity) {
        if (entity instanceof ScimGroup) return Type.GROUP;
        return Type.USER;
    }
}
