from dishka import Provider, Scope, provide

from agentic_shared.integrations.keycloak_admin.client import KeycloakAdminClientFactory
from agentic_shared.integrations.keycloak_admin.gateway import TenantGateway, UserGateway
from agentic_shared.integrations.keycloak_admin.settings import KeycloakAdminSettings


class KeycloakAdminProvider(Provider):
    scope = Scope.APP

    def __init__(self, settings: KeycloakAdminSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide
    def keycloak_admin_client_factory(self) -> KeycloakAdminClientFactory:
        return KeycloakAdminClientFactory(self._settings)

    @provide
    def tenant_gateway(self, factory: KeycloakAdminClientFactory) -> TenantGateway:
        return TenantGateway(self._settings, factory)

    @provide
    def user_gateway(self, factory: KeycloakAdminClientFactory) -> UserGateway:
        return UserGateway(self._settings, factory)
