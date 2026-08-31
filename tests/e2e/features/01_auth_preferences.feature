@e2e @ui @auth
Feature: Authentication and user preferences
  As a signed-in user
  I want to change language and theme from the profile menu
  So that the UI matches my preferences and I can sign out safely

  Background:
    Given I am signed in as "admin"

  @smoke
  Scenario: End-to-end preference journey then logout
    When I click the button "admin"
    And I choose "Magyar"
    Then I should see the heading "Dokumentumok"
    And local storage "app-locale" should be "hu"
    When I choose "Neptun"
    Then the page theme should be "neptune"
    And local storage "app-theme" should be "neptune"
    When I click the menu item "Kijelentkezés"
    Then I should be on a page matching "/realms/"

  @regression
  Scenario Outline: Switch UI language and see translated chrome
    When I click the button "admin"
    And I choose "<language_label>"
    Then I should see the heading "<documents_title>"
    And I should see the button "<upload_label>"

    Examples:
      | language_label | documents_title | upload_label   |
      | English        | Documents       | Upload PDF     |
      | Magyar         | Dokumentumok    | PDF feltöltés  |
      | Deutsch        | Dokumente       | PDF hochladen  |

  @regression
  Scenario: Theme selection persists on reload
    When I click the button "admin"
    And I choose "Neptune"
    And I reload the page
    Then the page theme should be "neptune"
