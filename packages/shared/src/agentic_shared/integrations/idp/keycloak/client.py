import logging

import httpx
from keycloak_admin_client import AuthenticatedClient
from pydantic import ValidationError

from agentic_shared.integrations.idp.keycloak.models import (
    AccessTokenResponse,
    ClientCredentialsTokenRequest,
)
from agentic_shared.integrations.idp.keycloak.settings import KeycloakAdminSettings

logger = logging.getLogger(__name__)


class KeycloakAdminClientFactory:
    def __init__(self, settings: KeycloakAdminSettings) -> None:
        self._settings = settings

    async def fetch_token(self) -> str:
        token_url = (
            f"{self._settings.keycloak_url.rstrip('/')}/realms/"
            f"{self._settings.keycloak_realm}/protocol/openid-connect/token"
        )
        request = ClientCredentialsTokenRequest(
            client_id=self._settings.keycloak_admin_client_id,
            client_secret=self._settings.keycloak_admin_client_secret.get_secret_value(),
        )
        async with httpx.AsyncClient(timeout=30.0) as http:
            response = await http.post(
                token_url,
                data=request.as_form(),
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
            try:
                token_payload = AccessTokenResponse.model_validate(response.json())
            except (ValidationError, ValueError, TypeError):
                logger.error("keycloak token response missing access_token")
                raise RuntimeError("Keycloak token response missing access_token") from None
            logger.info("fetched keycloak access token")
            return token_payload.access_token

    async def authenticated_client(self) -> AuthenticatedClient:
        token = await self.fetch_token()
        base = self._settings.keycloak_url.rstrip("/")
        return AuthenticatedClient(
            base_url=f"{base}/",
            token=token,
            raise_on_unexpected_status=True,
        )
