from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.infrastructure.core.client import open_client
from agentic_shared.infrastructure.redis.client import RedisClient
from agentic_shared.infrastructure.redis.protocols import RedisReader, RedisWriter
from agentic_shared.infrastructure.redis.settings import RedisSettings


class RedisProvider(Provider):
    def __init__(self, settings: RedisSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    async def redis_client(self) -> AsyncIterator[RedisClient]:
        async with open_client(RedisClient(self._settings)) as client:
            yield client

    @provide(scope=Scope.APP)
    def redis_reader(self, redis_client: RedisClient) -> RedisReader:
        return redis_client

    @provide(scope=Scope.APP)
    def redis_writer(self, redis_client: RedisClient) -> RedisWriter:
        return redis_client
