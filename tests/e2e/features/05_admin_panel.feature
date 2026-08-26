@e2e @ui @admin
Feature: Admin panel access
  As a tenant administrator
  I want to open the admin area from the profile menu
  So that I can manage tenants and users

  Background:
    Given the application is running with authentication enabled

  @smoke
  Scenario: Admin user opens admin panel and navigates sections
    Given I am signed in as an administrator
    When I open the account and preferences menu
    And I follow the admin panel link
    Then I should be on path "/admin"
    And I should see admin section "Tenants"
    And I should see admin section "Users"
    When I select admin section "Users"
    Then the admin users table or list should be visible

  Scenario: Non-admin cannot reach admin routes
    Given I am signed in as a non-admin user with write access
    When I navigate to "/admin"
    Then I should not see the admin tenants management UI
    And I should be redirected to the main chat view or see access denied

  Scenario: Admin panel shows tenant and user navigation
    Given I am signed in as an administrator
    When I navigate to "/admin"
    Then I should see admin section "Tenants"
    When I select admin section "Tenants"
    Then the admin tenants list should be visible
