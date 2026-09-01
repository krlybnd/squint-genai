@e2e @ui @documents @slow @regression
Feature: Document indexing status
  As a user who uploaded a PDF
  I want to see indexing progress in the sidebar
  So that I know when the file is searchable in chat

  Background:
    Given I am signed in as "admin"

  Scenario: Status transitions from pending to indexed
    Given the documents list is empty
    When I upload "sample_1.pdf"
    Then document "sample_1.pdf" should show "Pending" or "Indexing…"
    When I wait until document "sample_1.pdf" shows "Indexed" within 120 seconds
    Then I should see document "sample_1.pdf"

  Scenario: Open chunk viewer for an indexed document
    Given document "sample_1.pdf" shows "Indexed"
    When I open document "sample_1.pdf"
    Then I should see a dialog titled "sample_1.pdf"
