@e2e @ui @admin
Feature: Admin panel access
  As a tenant administrator
  I want to open the admin area from the profile menu
  So that I can manage tenants and users

  @smoke
  Scenario: Admin user opens admin panel and navigates sections
    Given I am signed in as "admin"
    When I click the button "admin"
    And I click the menu item "Admin panel"
    Then I should be on "/admin"
    And I should see the button "Tenants"
    And I should see the button "Users"
    When I click the button "Users"
    Then I should see the heading "Users"

  @regression
  Scenario: Non-admin cannot reach admin routes
    Given I am signed in as "writer@tenant-a.local"
    When I go to "/admin"
    Then I should not see "Administration"
    And I should be on "/"

  @regression
  Scenario: Admin panel shows tenant and user navigation
    Given I am signed in as "admin"
    When I go to "/admin"
    Then I should see the button "Tenants"
    When I click the button "Tenants"
    Then I should see the heading "Tenants"
