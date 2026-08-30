@api @guardrails @pii-vault
Feature: Index-time PII vault
  As a tenant user with contract documents
  I want PII tokenized at index time and detokenized via API
  So external embedding providers and Qdrant never store exact values

  Background:
    Given guardrails profile services are reachable
    And index-time PII tokenization prerequisites are met

  Scenario: Indexed chunks store tokens not plaintext
    Given a PDF with known PII is uploaded and indexed
    When I search retrieval for the known PII name
    Then the retrieval chunk text should not contain the plaintext PII
    And the retrieval chunk text should contain a vault token

  Scenario: Detokenize returns plaintext for same tenant
    Given a vault token from indexed PII content
    When I detokenize the vault token
    Then the detokenize response should contain the plaintext PII

  Scenario: Detokenize omits tokens for another tenant
    Given a vault token from indexed PII content
    When I detokenize the vault token as tenant B
    Then the detokenize response should be empty
