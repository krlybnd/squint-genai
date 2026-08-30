from typing import Any

import jwt
from jwt import PyJWKClient

from agentic_shared.crosscut.auth.settings import AuthSettings


class JwtValidator:
    """Validate Keycloak-issued RS256 access tokens via JWKS."""

    def __init__(self, settings: AuthSettings) -> None:
        self._settings = settings
        jwks_url = (
            f"{settings.keycloak_url.rstrip('/')}/realms/{settings.keycloak_realm}"
            "/protocol/openid-connect/certs"
        )
        self._jwks = PyJWKClient(jwks_url)

    def decode(self, token: str) -> dict[str, Any]:
        signing_key = self._jwks.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        if not isinstance(payload, dict):
            raise jwt.InvalidTokenError("JWT payload must be a JSON object")
        return payload
