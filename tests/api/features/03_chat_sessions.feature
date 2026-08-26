@api @smoke
Feature: Chat sessions
  As a caller of the chat API
  I want to create and list sessions through the published OpenAPI contract
  So that a conversation can start without the UI

  Scenario: Create a session then see it in the list
    When I create a chat session titled "api-happy-path"
    Then the session should have an id
    When I list chat sessions
    Then the session list should include that session
