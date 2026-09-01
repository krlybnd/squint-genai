@api @auth
Feature: Bound HTTP authentication and tenant isolation
  As a caller of the live API with AUTH_MODE=jwt
  I want 401 without a token, 403 without the role, and tenant-scoped documents
  So that access control is evidenced by HTTP, not a skipped regulation matrix

  Background:
    Given JWT authentication is enforced

  Scenario: Missing bearer is unauthorized
    When I GET "/v1/documents" without a bearer token
    Then the HTTP status should be 401

  Scenario: Read-only user cannot presign an upload
    When I presign an upload as "reader@tenant-a.local"
    Then the HTTP status should be 403

  Scenario: Read-only user cannot list tenants on admin
    When I GET "/v1/tenants" on admin as "reader@tenant-a.local"
    Then the HTTP status should be 403

  Scenario: Tenant B cannot read a Tenant A document
    Given a document presigned as "alice@tenant-a.local"
    When I GET that document as "bob@tenant-b.local"
    Then the HTTP status should be 404
    When I GET that document as "alice@tenant-a.local"
    Then the HTTP status should be 200

  Scenario: Spoofed X-Tenant-Id does not override JWT tenant_id
    Given a document presigned as "alice@tenant-a.local"
    When I GET that document as "alice@tenant-a.local" with header X-Tenant-Id "tenant-b"
    Then the HTTP status should be 200
