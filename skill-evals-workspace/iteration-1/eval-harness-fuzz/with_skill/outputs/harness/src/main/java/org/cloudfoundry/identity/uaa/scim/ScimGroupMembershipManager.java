package org.cloudfoundry.identity.uaa.scim;

import java.util.List;
import java.util.Set;

/**
 * Stub interface — extracted from:
 *   server/src/main/java/org/cloudfoundry/identity/uaa/scim/ScimGroupMembershipManager.java
 *
 * Methods called by createGroup():
 *   membershipManager.addMember(groupId, member, zoneId)
 *   membershipManager.getMembers(groupId, false, zoneId)
 */
public interface ScimGroupMembershipManager {

    ScimGroupMember addMember(String groupId, ScimGroupMember member, String zoneId);

    List<ScimGroupMember> getMembers(String groupId, boolean includeEntities, String zoneId);

    // --- Remaining methods not called by createGroup — stub signatures only ---

    Set<ScimGroup> getGroupsWithMember(String memberId, boolean transitive, String zoneId);

    ScimGroupMember getMemberById(String groupId, String memberId, String zoneId);

    List<ScimGroupMember> updateOrAddMembers(String groupId, List<ScimGroupMember> members, String zoneId);

    ScimGroupMember removeMemberById(String groupId, String memberId, String zoneId);

    List<ScimGroupMember> removeMembersByGroupId(String groupId, String zoneId);

    Set<ScimGroup> removeMembersByMemberId(String memberId, String zoneId);

    Set<ScimGroup> removeMembersByMemberId(String memberId, String origin, String zoneId);

    void deleteMembersByOrigin(String origin, String zoneId);

    Set<ScimGroup> getGroupsWithExternalMember(String memberId, String origin, String zoneId);
}
