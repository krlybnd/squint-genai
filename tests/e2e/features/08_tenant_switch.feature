@e2e @ui @auth
Feature: Switch active tenant from the profile menu
  As a user who belongs to more than one tenant
  I want to change the active tenant from the avatar menu
  So that documents and chat stay scoped to the tenant I pick

  Background:
    Given I am signed in as "admin"

  @regression
  Scenario: Switching tenant hides the other tenant's documents
    When I click the button "admin"
    And I choose "Tenant B" from "Tenant"
    Given the documents list is empty
    When I click the button "admin"
    And I choose "Tenant A" from "Tenant"
    Given the documents list is empty
    When I upload "sample_1.pdf"
    Then I should see document "sample_1.pdf"
    When I click the button "admin"
    And I choose "Tenant B" from "Tenant"
    Then I should see "Tenant B"
    And I should not see document "sample_1.pdf"
    When I choose "Tenant A" from "Tenant"
    Then I should see "Tenant A"
    And I should see document "sample_1.pdf"
