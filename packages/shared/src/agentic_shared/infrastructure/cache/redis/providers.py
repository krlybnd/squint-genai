from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.infrastructure.cache.core.protocols import CacheReader, CacheWriter
from agentic_shared.infrastructure.cache.redis.client import RedisClient
from agentic_shared.infrastructure.cache.redis.settings import RedisSettings


class RedisProvider(Provider):
    def __init__(self, settings: RedisSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    async def redis_client(self) -> AsyncIterator[RedisClient]:
        async with RedisClient(self._settings) as client:
            yield client

    @provide(scope=Scope.APP)
    def cache_reader(self, redis_client: RedisClient) -> CacheReader:
        return redis_client

    @provide(scope=Scope.APP)
    def cache_writer(self, redis_client: RedisClient) -> CacheWriter:
        return redis_client
