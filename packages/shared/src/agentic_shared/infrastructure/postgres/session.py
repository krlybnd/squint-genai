from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from agentic_shared.infrastructure.postgres.settings import DatabaseSettings


def create_session_factory(settings: DatabaseSettings) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(settings.database_url, echo=False)
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session
