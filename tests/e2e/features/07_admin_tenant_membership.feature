@e2e @ui @admin
Feature: Admin tenant membership and per-tenant roles
  As a tenant administrator
  I want to assign users to tenants with roles from the user editor
  And see the same membership reflected on the tenant members panel

  Background:
    Given the application is running with authentication enabled

  Scenario: Assign new tenant to alice with read and write roles
    Given I am signed in as an administrator
    When I navigate to "/admin"
    And I select admin section "Tenants"
    And I create a unique tenant for membership testing
    When I select admin section "Users"
    And I open the admin user editor for "alice@tenant-a.local"
    And I assign the e2e tenant to the current user
    And I set roles "read" and "write" for the e2e tenant on the user membership
    And I close the admin modal
    When I select admin section "Tenants"
    And I open the e2e tenant for editing
    Then the tenant members should include "alice@tenant-a.local" with roles "read" and "write"
