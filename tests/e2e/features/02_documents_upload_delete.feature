@e2e @ui @documents
Feature: Document upload and deletion
  As a user with write access
  I want to upload PDFs and remove them from the sidebar
  So that I control what is indexed in my tenant

  Background:
    Given I am signed in as "admin"

  @smoke
  Scenario: Upload a PDF and delete it from the actions menu
    Given the documents list is empty
    When I upload "sample_1.pdf"
    Then I should see document "sample_1.pdf"
    When I open "Document actions" on document "sample_1.pdf"
    And I click the button "Delete"
    Then I should not see document "sample_1.pdf"
    And I should see "No documents yet"

  @regression
  Scenario: Upload button is hidden for read-only users
    Given I am signed in as "bob@tenant-b.local"
    When I go to "/"
    Then I should not see the button "Upload PDF"
    And I should see "Read-only access"

  @regression
  Scenario: Document actions menu offers revectorization and delete
    Given the documents list is empty
    And the document "sample_2.pdf" is in the sidebar
    When I open "Document actions" on document "sample_2.pdf"
    Then I should see document action "Revectorization"
    And I should see document action "Delete"
