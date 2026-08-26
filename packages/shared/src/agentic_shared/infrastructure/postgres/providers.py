from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.infrastructure.core.client import open_client
from agentic_shared.infrastructure.postgres.client import DatabaseClient
from agentic_shared.infrastructure.postgres.settings import DatabaseSettings


class DatabaseProvider(Provider):
    def __init__(self, settings: DatabaseSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    async def database_client(self) -> AsyncIterator[DatabaseClient]:
        async with open_client(DatabaseClient(self._settings)) as client:
            yield client
