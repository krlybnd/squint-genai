from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.infrastructure.sql.postgres.client import DatabaseClient
from agentic_shared.infrastructure.sql.postgres.settings import DatabaseSettings


class DatabaseProvider(Provider):
    def __init__(self, settings: DatabaseSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    async def database_client(self) -> AsyncIterator[DatabaseClient]:
        async with DatabaseClient(self._settings) as client:
            yield client
