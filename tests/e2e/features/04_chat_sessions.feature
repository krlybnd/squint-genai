@e2e @ui @chat
Feature: Chat sessions and messaging
  As a user with write access
  I want to start chats and manage saved sessions
  So that I can converse with my document knowledge base

  Background:
    Given the application is running with authentication enabled
    And I am signed in as a user with write access

  @smoke
  Scenario: New chat shows empty state and input
    When I start a new chat from the toolbar
    Then the chat empty title should be visible
    And the chat input placeholder should be "Ask a question…"

  Scenario: Send a message and receive an assistant reply
    When I start a new chat from the toolbar
    And I send the chat message "What documents are available?"
    Then I should see my message "What documents are available?" in the thread
    And I should receive an assistant reply within 90 seconds

  Scenario: Session drawer lists and deletes a conversation
    When I open the sessions drawer
    And I start a new chat from the toolbar
    And I send the chat message "Hello E2E session"
    And I wait until chat is not streaming
    And I open the sessions drawer
    Then the sessions list should contain a session with title matching "E2E Session Introduction"
    When I wait until the active session can be deleted
    And I delete the current chat session from the drawer
    Then no chat error should be visible
    And the current chat session should not appear in the sessions list
