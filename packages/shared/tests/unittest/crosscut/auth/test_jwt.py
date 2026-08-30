import unittest
from unittest.mock import MagicMock, patch

import jwt

from agentic_shared.crosscut.auth.jwt import JwtValidator
from agentic_shared.crosscut.auth.settings import AuthSettings


class TestJwtValidator(unittest.TestCase):
    def test_decode_returns_claims(self) -> None:
        settings = AuthSettings(
            keycloak_url="http://keycloak:8080",
            keycloak_realm="agentic-rag-eval",
        )
        signing_key = MagicMock()
        signing_key.key = "pem"
        with (
            patch("agentic_shared.crosscut.auth.jwt.PyJWKClient") as jwks_cls,
            patch(
                "agentic_shared.crosscut.auth.jwt.jwt.decode",
                return_value={"sub": "u1"},
            ) as decode,
        ):
            jwks_cls.return_value.get_signing_key_from_jwt.return_value = signing_key
            validator = JwtValidator(settings)
            self.assertEqual(validator.decode("token"), {"sub": "u1"})
            decode.assert_called_once()
            jwks_cls.assert_called_once_with(
                "http://keycloak:8080/realms/agentic-rag-eval/protocol/openid-connect/certs"
            )

    def test_decode_rejects_non_object_payload(self) -> None:
        settings = AuthSettings(
            keycloak_url="http://keycloak:8080/",
            keycloak_realm="r",
        )
        signing_key = MagicMock()
        signing_key.key = "pem"
        with (
            patch("agentic_shared.crosscut.auth.jwt.PyJWKClient") as jwks_cls,
            patch(
                "agentic_shared.crosscut.auth.jwt.jwt.decode",
                return_value="not-a-dict",
            ),
        ):
            jwks_cls.return_value.get_signing_key_from_jwt.return_value = signing_key
            with self.assertRaises(jwt.InvalidTokenError):
                JwtValidator(settings).decode("token")
