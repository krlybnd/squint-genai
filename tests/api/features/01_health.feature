@api @smoke
Feature: Service health
  As an operator
  I want each service health endpoint to answer
  So that I know the stack is up before running journeys

  Scenario: API health is ok
    When I request API health
    Then the health status should be "ok"

  Scenario: Chat health is ok
    When I request chat health
    Then the health status should be "ok"

  Scenario: Admin health is ok
    When I request admin health
    Then the health status should be "ok"
