from agentic_shared.integrations.keycloak_admin.gateway import UserGateway
from dishka import Provider, Scope, provide

from agentic_admin.modules.users.service import UserAdminService


class UsersProvider(Provider):
    scope = Scope.APP

    @provide
    def user_admin_service(self, gateway: UserGateway) -> UserAdminService:
        return UserAdminService(gateway)
