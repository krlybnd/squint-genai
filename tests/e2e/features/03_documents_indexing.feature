@e2e @ui @documents @slow
Feature: Document indexing status
  As a user who uploaded a PDF
  I want to see indexing progress in the sidebar
  So that I know when the file is searchable in chat

  Background:
    Given the application is running with authentication enabled
    And I am signed in as a user with write access
    And the stack indexing worker is running

  Scenario: Status transitions from pending to indexed
    When I upload the fixture file "sample.pdf" from the documents panel
    Then document "sample.pdf" should show status "Pending" or "Indexing…"
    When I wait until document "sample.pdf" shows status "Indexed" within 120 seconds
    Then the document card "sample.pdf" should be clickable

  Scenario: Open chunk viewer for an indexed document
    Given document "sample.pdf" shows status "Indexed"
    When I open document "sample.pdf" from the sidebar
    Then the chunk viewer modal should be visible for "sample.pdf"
