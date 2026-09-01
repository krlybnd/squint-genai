@prep
Feature: Prepare Bob's tenant before the walkthrough recording
  As the demo operator
  I want the three investigation PDFs already indexed in Tenant B
  So the recorded tour never waits on upload or Celery

  # Not part of the video. Fast. No captions. No human mouse.
  # Upload Alpha+Beta first so indexing starts, then Gamma; wait for all three.
  # PDFs: resources/eval/investigation-dossier-{alpha,beta,gamma-decoy}.pdf
  # Run this before @demo. See #52.

  Scenario: Index all three dossiers in Tenant B
    Given I am signed in as "admin"
    When I go to "/"
    And I click the button "admin"
    And I choose "Tenant B" from "Organisation"
    And the documents list is empty
    When I upload "investigation-dossier-alpha.pdf"
    And I upload "investigation-dossier-beta.pdf"
    And I upload "investigation-dossier-gamma-decoy.pdf"
    Then I should see document "investigation-dossier-alpha.pdf"
    And I should see document "investigation-dossier-beta.pdf"
    And I should see document "investigation-dossier-gamma-decoy.pdf"
    When I wait until document "investigation-dossier-alpha.pdf" shows "Indexed" within 180 seconds
    And I wait until document "investigation-dossier-beta.pdf" shows "Indexed" within 180 seconds
    And I wait until document "investigation-dossier-gamma-decoy.pdf" shows "Indexed" within 180 seconds
