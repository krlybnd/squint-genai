@e2e @ui @chat
Feature: Chat sessions and messaging
  As a user with write access
  I want to start chats and manage saved sessions
  So that I can converse with my document knowledge base

  Background:
    Given I am signed in as "admin"

  @smoke
  Scenario: New chat shows empty state and input
    When I click the button "New chat"
    Then I should see "Ask anything about your documents"
    And I should see the placeholder "Ask a question…"

  @regression @slow
  Scenario: Send a message and receive an assistant reply
    Given the document "sample_1.pdf" is in the sidebar
    And document "sample_1.pdf" shows "Indexed"
    When I click the button "New chat"
    And I type "Who won the Pineford pie contest?" into "Ask a question…" and press Enter
    Then I should see "Who won the Pineford pie contest?"
    And I should see an assistant reply within 90 seconds

  @regression
  Scenario: Session drawer lists and deletes a conversation
    Given the sessions list is empty
    When I click the button "Open sessions"
    And I click the button "New chat"
    And I type "Hello E2E session" into "Ask a question…" and press Enter
    And I wait until generation has stopped
    And I wait until the session title is not "New chat"
    And I click the button "Open sessions"
    Then the sessions list should contain the current session
    When I wait until the current session can be deleted
    And I delete the current session
    Then I should not see a chat error
    And the current session should not be in the sessions list
