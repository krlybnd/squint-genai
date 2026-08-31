from agentic_shared.integrations.idp.core import TenantAdmin, UserAdmin
from dishka import Provider, Scope, provide

from agentic_admin.modules.me.service import MeService


class MeProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def me_service(self, users: UserAdmin, tenants: TenantAdmin) -> MeService:
        return MeService(users, tenants)
