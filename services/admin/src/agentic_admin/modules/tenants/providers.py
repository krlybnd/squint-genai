from agentic_shared.integrations.keycloak_admin.gateway import TenantGateway, UserGateway
from dishka import Provider, Scope, provide

from agentic_admin.modules.tenants.service import TenantAdminService


class TenantsProvider(Provider):
    scope = Scope.APP

    @provide
    def tenant_admin_service(
        self, tenant_gateway: TenantGateway, user_gateway: UserGateway
    ) -> TenantAdminService:
        return TenantAdminService(tenant_gateway, user_gateway)
