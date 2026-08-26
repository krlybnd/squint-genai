import logging

import httpx
from keycloak_admin_client import AuthenticatedClient

from agentic_shared.integrations.keycloak_admin.settings import KeycloakAdminSettings

logger = logging.getLogger(__name__)


class KeycloakAdminClientFactory:
    def __init__(self, settings: KeycloakAdminSettings) -> None:
        self._settings = settings

    async def fetch_token(self) -> str:
        token_url = (
            f"{self._settings.keycloak_url.rstrip('/')}/realms/"
            f"{self._settings.keycloak_realm}/protocol/openid-connect/token"
        )
        async with httpx.AsyncClient(timeout=30.0) as http:
            response = await http.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._settings.keycloak_admin_client_id,
                    "client_secret": self._settings.keycloak_admin_client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError:
                logger.warning(
                    "keycloak token request failed status=%s",
                    response.status_code,
                )
                raise
            payload = response.json()
            token = payload.get("access_token")
            if not isinstance(token, str) or not token:
                logger.error("keycloak token response missing access_token")
                raise RuntimeError("Keycloak token response missing access_token")
            return token

    async def authenticated_client(self) -> AuthenticatedClient:
        token = await self.fetch_token()
        base = self._settings.keycloak_url.rstrip("/")
        return AuthenticatedClient(
            base_url=f"{base}/",
            token=token,
            raise_on_unexpected_status=True,
        )
