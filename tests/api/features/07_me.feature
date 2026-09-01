@api @auth @me
Feature: Caller tenancy without org-catalog privileges
  As a JWT caller of GET /v1/me
  I want membership from the per-user Keycloak org endpoint
  So that the api service account can stay off manage-realm

  Background:
    Given JWT authentication is enforced

  Scenario: Member can read their tenancy
    When I GET my profile as "alice@tenant-a.local"
    Then the HTTP status should be 200
    And my profile tenant_id should be "tenant-a"
    And my profile tenants should include "tenant-a"

  Scenario: Member can write their active tenant
    When I set my active tenant to "tenant-a" as "alice@tenant-a.local"
    Then the HTTP status should be 200
    And my profile tenant_id should be "tenant-a"

  Scenario: Missing bearer on my profile is unauthorized
    When I GET my profile without a bearer token
    Then the HTTP status should be unauthorized
