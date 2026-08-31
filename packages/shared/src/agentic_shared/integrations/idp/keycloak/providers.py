from dishka import Provider, Scope, provide

from agentic_shared.integrations.idp.core.protocols import (
    TenantAdmin,
    UserAdmin,
    UserTenancyRead,
    UserTenancyWrite,
)
from agentic_shared.integrations.idp.keycloak.client import KeycloakAdminClientFactory
from agentic_shared.integrations.idp.keycloak.settings import KeycloakAdminSettings
from agentic_shared.integrations.idp.keycloak.tenant.gateway import TenantGateway
from agentic_shared.integrations.idp.keycloak.user.gateway import UserGateway
from agentic_shared.integrations.idp.keycloak.user.tenancy import KeycloakUserTenancy


class KeycloakAdminProvider(Provider):
    scope = Scope.APP

    def __init__(self, settings: KeycloakAdminSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide
    def keycloak_admin_client_factory(self) -> KeycloakAdminClientFactory:
        return KeycloakAdminClientFactory(self._settings)

    @provide
    def tenant_admin(self, factory: KeycloakAdminClientFactory) -> TenantAdmin:
        return TenantGateway(self._settings, factory)

    @provide
    def user_admin(self, factory: KeycloakAdminClientFactory) -> UserAdmin:
        return UserGateway(self._settings, factory)


class KeycloakUserTenancyProvider(Provider):
    """API-facing tenancy: UserTenancyRead.get / UserTenancyWrite.set_active only."""

    scope = Scope.APP

    def __init__(self, settings: KeycloakAdminSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide
    def keycloak_admin_client_factory(self) -> KeycloakAdminClientFactory:
        return KeycloakAdminClientFactory(self._settings)

    @provide
    def user_tenancy_read(self, factory: KeycloakAdminClientFactory) -> UserTenancyRead:
        return self._tenancy(factory)

    @provide
    def user_tenancy_write(self, factory: KeycloakAdminClientFactory) -> UserTenancyWrite:
        return self._tenancy(factory)

    def _tenancy(self, factory: KeycloakAdminClientFactory) -> KeycloakUserTenancy:
        return KeycloakUserTenancy(
            UserGateway(self._settings, factory),
            TenantGateway(self._settings, factory),
        )
