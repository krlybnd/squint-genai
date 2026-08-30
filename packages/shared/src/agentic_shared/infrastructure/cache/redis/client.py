import redis

from agentic_shared.infrastructure.cache.core.protocols import CacheReader, CacheWriter
from agentic_shared.infrastructure.cache.redis.settings import RedisSettings
from agentic_shared.infrastructure.core.client import InfrastructureClient


class RedisClient(InfrastructureClient[RedisSettings], CacheReader, CacheWriter):
    def __init__(self, settings: RedisSettings) -> None:
        super().__init__(settings)
        self._client = redis.from_url(settings.redis_url)

    async def health_check(self) -> bool:
        return self.ping()

    def close(self) -> None:
        try:
            self._client.close()
        finally:
            super().close()

    def ping(self) -> bool:
        try:
            return bool(self._client.ping())
        except redis.RedisError:
            self._logger.debug("%s health check failed", self.title, exc_info=True)
            return False

    def get(self, key: str) -> bytes | None:
        value = self._client.get(key)
        return value if isinstance(value, bytes) else None

    def set(self, key: str, value: bytes | str, *, ex: int | None = None) -> None:
        self._client.set(key, value, ex=ex)

    def delete(self, key: str) -> None:
        self._client.delete(key)
