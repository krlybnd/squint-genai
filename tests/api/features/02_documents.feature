@api @smoke
Feature: Documents list
  As a caller of the documents API
  I want to list documents through the published OpenAPI contract
  So that the catalog endpoint is usable

  Scenario: List documents returns the catalog envelope
    When I list documents
    Then the document list should include items and a total
