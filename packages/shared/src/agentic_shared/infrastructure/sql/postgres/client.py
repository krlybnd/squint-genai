from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from agentic_shared.infrastructure.core.client import InfrastructureClient
from agentic_shared.infrastructure.sql.postgres.settings import DatabaseSettings


class DatabaseClient(InfrastructureClient[DatabaseSettings]):
    def __init__(self, settings: DatabaseSettings) -> None:
        super().__init__(settings)
        self._engine: AsyncEngine = create_async_engine(settings.database_url, echo=False)

    async def health_check(self) -> bool:
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            self._logger.debug("%s health check failed", self.title, exc_info=True)
            return False

    async def aclose(self) -> None:
        try:
            await self._engine.dispose()
        finally:
            await super().aclose()
