package org.cloudfoundry.identity.uaa.zone.beans;

/**
 * Stub interface — extracted from:
 *   server/src/main/java/org/cloudfoundry/identity/uaa/zone/beans/IdentityZoneManager.java
 *
 * Only getCurrentIdentityZoneId() is called by createGroup().
 * The remaining methods are stubs.
 */
public interface IdentityZoneManager {
    String getCurrentIdentityZoneId();

    // Stubs — not called by createGroup
    boolean isCurrentZoneUaa();
}
