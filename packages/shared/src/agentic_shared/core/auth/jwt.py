from typing import Any

import jwt
from jwt import PyJWKClient

from agentic_shared.core.auth.settings import AuthSettings


class JwtValidator:
    def __init__(self, settings: AuthSettings) -> None:
        self._settings = settings
        jwks_url = (
            f"{settings.keycloak_url.rstrip('/')}/realms/{settings.keycloak_realm}"
            "/protocol/openid-connect/certs"
        )
        self._jwks = PyJWKClient(jwks_url)

    def decode(self, token: str) -> dict[str, Any]:
        signing_key = self._jwks.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
