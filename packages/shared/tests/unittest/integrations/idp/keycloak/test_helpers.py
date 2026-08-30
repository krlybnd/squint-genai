from __future__ import annotations

import json
import sys
import unittest
from http import HTTPStatus
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentic_shared.integrations.idp.keycloak import (  # noqa: E402
    _check_response,
    _decode_error,
    _location_resource_id,
)
from agentic_shared.integrations.idp.keycloak.errors import (  # noqa: E402
    KeycloakAdminError,
    KeycloakConflictError,
    KeycloakForbiddenError,
    KeycloakNotFoundError,
)


class TestKeycloakHelpers(unittest.TestCase):
    def test_location_resource_id_parses_trailing_segment(self) -> None:
        headers = {
            "Location": "https://keycloak/admin/realms/demo/organizations/org-uuid-123",
        }
        self.assertEqual(_location_resource_id(headers), "org-uuid-123")

    def test_location_resource_id_accepts_lowercase_header(self) -> None:
        headers = {"location": "http://kc/users/user-42/"}
        self.assertEqual(_location_resource_id(headers), "user-42")

    def test_location_resource_id_returns_none_when_missing(self) -> None:
        self.assertIsNone(_location_resource_id({}))

    def test_decode_error_prefers_error_message_json_field(self) -> None:
        content = json.dumps({"errorMessage": "User exists"}).encode()
        self.assertEqual(_decode_error(content), "User exists")

    def test_decode_error_falls_back_to_error_field(self) -> None:
        content = json.dumps({"error": "invalid_grant"}).encode()
        self.assertEqual(_decode_error(content), "invalid_grant")

    def test_decode_error_empty_content(self) -> None:
        self.assertEqual(_decode_error(b""), "Keycloak request failed")

    def test_decode_error_non_json_bytes(self) -> None:
        self.assertEqual(_decode_error(b"plain text failure"), "plain text failure")

    def test_check_response_accepts_success_statuses(self) -> None:
        for status in (HTTPStatus.OK, HTTPStatus.CREATED, HTTPStatus.NO_CONTENT):
            _check_response(status, b"")

    def test_check_response_raises_not_found(self) -> None:
        with self.assertRaises(KeycloakNotFoundError):
            _check_response(HTTPStatus.NOT_FOUND, b'{"errorMessage":"missing"}')

    def test_check_response_raises_conflict(self) -> None:
        with self.assertRaises(KeycloakConflictError):
            _check_response(HTTPStatus.CONFLICT, b'{"errorMessage":"exists"}')

    def test_check_response_raises_forbidden(self) -> None:
        with self.assertRaises(KeycloakForbiddenError):
            _check_response(HTTPStatus.FORBIDDEN, b'{"errorMessage":"denied"}')

    def test_check_response_raises_generic_admin_error(self) -> None:
        with self.assertRaises(KeycloakAdminError) as ctx:
            _check_response(HTTPStatus.BAD_REQUEST, b'{"errorMessage":"bad input"}')
        self.assertIn("400", str(ctx.exception))
