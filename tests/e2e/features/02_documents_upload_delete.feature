@e2e @ui @documents
Feature: Document upload and deletion
  As a user with write access
  I want to upload PDFs and remove them from the sidebar
  So that I control what is indexed in my tenant

  Background:
    Given the application is running with authentication enabled
    And I am signed in as a user with write access
    And the documents list is loaded

  @smoke
  Scenario: Upload a PDF and delete it from the actions menu
    When I upload the fixture file "sample.pdf" from the documents panel
    Then a document card named "sample.pdf" should appear in the sidebar
    When I open actions for document "sample.pdf"
    And I choose delete document
    Then document "sample.pdf" should not appear in the sidebar
    And the empty documents hint should be visible

  Scenario: Upload button is hidden for read-only users
    Given I am signed in as a read-only user
    When the documents list is loaded
    Then the upload PDF control should not be visible
    And the read-only empty hint should be visible

  Scenario: Document actions menu offers revectorization and delete
    Given a document "sample.pdf" exists in the sidebar
    When I open actions for document "sample.pdf"
    Then I should see document action "Revectorization"
    And I should see document action "Delete"
