from __future__ import annotations

from keycloak_admin_client import AuthenticatedClient

from agentic_shared.integrations.idp.keycloak.client import KeycloakAdminClientFactory
from agentic_shared.integrations.idp.keycloak.settings import KeycloakAdminSettings


class KeycloakGatewayBase:
    def __init__(
        self, settings: KeycloakAdminSettings, factory: KeycloakAdminClientFactory
    ) -> None:
        self._settings = settings
        self._factory = factory

    @property
    def _realm(self) -> str:
        return self._settings.keycloak_realm

    async def _client(self) -> AuthenticatedClient:
        return await self._factory.authenticated_client()
