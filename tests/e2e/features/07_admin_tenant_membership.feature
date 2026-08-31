@e2e @ui @admin @regression
Feature: Admin tenant membership and per-tenant roles
  As a tenant administrator
  I want to assign users to tenants with roles from the user editor
  And see the same membership reflected on the tenant members panel

  Scenario: Assign new tenant to alice with read and write roles
    Given I am signed in as "admin"
    When I go to "/admin"
    And I click the button "Tenants"
    And I create a unique tenant with alias prefix "e2e" and name prefix "E2E membership"
    When I click the button "Users"
    And I open the row "alice@tenant-a.local"
    And I assign the last created tenant
    And I set membership roles "read, write"
    And I close the dialog
    When I click the button "Tenants"
    And I open the last created tenant
    Then the member "alice@tenant-a.local" should have roles "read, write"
