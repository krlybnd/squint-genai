from agentic_shared.integrations.idp.core import UserTenancyRead, UserTenancyWrite
from dishka import Provider, Scope, provide

from agentic_api.modules.me.service import MeService


class MeProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def me_service(self, reader: UserTenancyRead, writer: UserTenancyWrite) -> MeService:
        return MeService(reader, writer)
