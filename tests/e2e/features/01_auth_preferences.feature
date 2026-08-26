@e2e @ui @auth
Feature: Authentication and user preferences
  As a signed-in user
  I want to change language and theme from the profile menu
  So that the UI matches my preferences and I can sign out safely

  Background:
    Given the application is running with authentication enabled
    And I am signed in as a user with write access

  @smoke
  Scenario: End-to-end preference journey then logout
    When I open the account and preferences menu
    And I select language "Magyar"
    Then the documents sidebar heading should be "Dokumentumok"
    And local storage key "app-locale" should be "hu"
    When I select theme "Neptun"
    Then the document root should have theme "neptune"
    And local storage key "app-theme" should be "neptune"
    When I sign out from the profile menu
    Then I should be on the Keycloak login page

  Scenario Outline: Switch UI language and see translated chrome
    When I open the account and preferences menu
    And I select language "<language_label>"
    Then the documents sidebar heading should be "<documents_title>"
    And the upload action should show "<upload_label>"

    Examples:
      | language_label | documents_title | upload_label   |
      | English        | Documents       | Upload PDF     |
      | Magyar         | Dokumentumok    | PDF feltöltés  |
      | Deutsch        | Dokumente       | PDF hochladen  |

  Scenario: Theme selection persists on reload
    When I open the account and preferences menu
    And I select theme "Neptune"
    And I reload the page
    Then the document root should have theme "neptune"
