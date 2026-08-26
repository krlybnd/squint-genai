@api @smoke
Feature: Admin catalog
  As a caller of the admin API
  I want to list tenants and users through the published OpenAPI contract
  So that the admin service is usable without the UI

  Scenario: List tenants returns an items envelope
    When I list tenants
    Then the tenant list should include items

  Scenario: List users returns an items envelope
    When I list users
    Then the user list should include items
