from agentic_shared.integrations.idp.core import TenantAdmin, UserAdmin
from dishka import Provider, Scope, provide

from agentic_admin.modules.tenants.service import TenantAdminService


class TenantsProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def tenant_admin_service(
        self, tenant_gateway: TenantAdmin, user_gateway: UserAdmin
    ) -> TenantAdminService:
        return TenantAdminService(tenant_gateway, user_gateway)
