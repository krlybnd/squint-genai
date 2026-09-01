@api @smoke
Feature: AI system card
  As a caller of the documents API
  I want the published AI system-card JSON
  So that EU AI Act transparency is an HTTP contract, not a skip-listed article

  Scenario: System card returns the declared AI metadata
    When I GET the AI system card
    Then the system card should include name purpose risk tier and oversight
