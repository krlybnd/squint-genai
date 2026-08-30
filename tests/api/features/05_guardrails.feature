@api @guardrails
Feature: Guardrails hard rejects
  As a caller of chat and annotations APIs
  I want deterministic BanSubstrings rejects for banned obscenity
  So that guardrails behavior is visible without relying on ML thresholds

  Background:
    Given guardrails profile services are reachable

  Scenario: Chat stream refuses a banned obscenity phrase
    When I stream a chat message containing the banned obscenity phrase
    Then the chat stream should refuse with a guard block

  Scenario: Chat stream continues for a clean message
    When I stream a clean chat message for guardrails
    Then the chat stream should pass the guard node

  Scenario: Chunk comment with banned obscenity is rejected
    Given an indexed chunk is available for comments
    When I submit a chunk comment containing the banned obscenity phrase
    Then the chunk comment should be rejected by the guard

  Scenario: Clean chunk comment is accepted
    Given an indexed chunk is available for comments
    When I submit a clean chunk comment for guardrails
    Then the chunk comment should be accepted
