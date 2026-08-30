from agentic_shared.integrations.idp.core import UserAdmin
from dishka import Provider, Scope, provide

from agentic_admin.modules.users.service import UserAdminService


class UsersProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def user_admin_service(self, gateway: UserAdmin) -> UserAdminService:
        return UserAdminService(gateway)
