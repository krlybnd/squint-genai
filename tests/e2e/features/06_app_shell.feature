@e2e @ui @shell
Feature: Main application shell
  As an authenticated user
  I want a consistent layout with documents sidebar and chat area
  So that I can upload files and chat in one place

  Background:
    Given the application is running with authentication enabled
    And I am signed in as a user with write access

  @smoke
  Scenario: Home layout shows documents sidebar and chat panel
    When I navigate to "/"
    Then the documents sidebar heading should be "Documents"
    And the chat empty title should be visible
    And the profile menu trigger should show my username

  Scenario: Session drawer toggles without losing sidebar
    When I open the sessions drawer
    Then the sessions panel title should be "Sessions"
    And the documents sidebar heading should be "Documents"
    When I close the sessions drawer
    Then the sessions panel should be hidden

  Scenario: App title and theme default on first visit
    Given local storage is cleared for locale and theme
    When I navigate to "/"
    Then the document root should have theme "purple"
    And the documents sidebar heading should be "Documents"
