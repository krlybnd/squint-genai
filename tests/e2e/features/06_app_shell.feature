@e2e @ui @shell
Feature: Main application shell
  As an authenticated user
  I want a consistent layout with documents sidebar and chat area
  So that I can upload files and chat in one place

  Background:
    Given I am signed in as "admin"

  @smoke
  Scenario: Home layout shows documents sidebar and chat panel
    When I go to "/"
    Then I should see the heading "Documents"
    And I should see "Ask anything about your documents"
    And I should see the username "admin"

  @regression
  Scenario: Session drawer toggles without losing sidebar
    When I click the button "Open sessions"
    Then I should see the heading "Sessions"
    And I should see the heading "Documents"
    When I click the button "Close sessions"
    Then the sessions drawer should be closed

  @regression
  Scenario: App title and theme default on first visit
    Given I clear local storage keys "app-locale, app-theme"
    When I go to "/"
    Then the page theme should be "purple"
    And I should see the heading "Documents"
