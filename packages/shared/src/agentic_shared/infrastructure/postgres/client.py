from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from agentic_shared.infrastructure.core.client import BaseInfraClient, open_client
from agentic_shared.infrastructure.postgres.settings import DatabaseSettings


class DatabaseClient(BaseInfraClient[DatabaseSettings]):
    def __init__(self, settings: DatabaseSettings) -> None:
        super().__init__(settings)
        self._engine: AsyncEngine = create_async_engine(settings.database_url, echo=False)

    async def health_check(self) -> bool:
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def aclose(self) -> None:
        try:
            await self._engine.dispose()
        finally:
            await super().aclose()


@asynccontextmanager
async def database_client(settings: DatabaseSettings):
    async with open_client(DatabaseClient(settings)) as client:
        yield client
