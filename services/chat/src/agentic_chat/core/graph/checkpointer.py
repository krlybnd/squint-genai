from contextlib import AbstractAsyncContextManager

from agentic_shared.infrastructure.postgres.settings import DatabaseSettings
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

_saver: AsyncPostgresSaver | None = None
_context_manager: AbstractAsyncContextManager[AsyncPostgresSaver] | None = None


async def get_checkpointer(database: DatabaseSettings) -> BaseCheckpointSaver:
    global _saver, _context_manager
    if _saver is not None:
        return _saver

    conn = database.checkpoint_postgres_url()
    _context_manager = AsyncPostgresSaver.from_conn_string(conn)
    saver = await _context_manager.__aenter__()
    await saver.setup()
    _saver = saver
    return saver


async def close_checkpointer() -> None:
    global _saver, _context_manager
    if _context_manager is not None:
        await _context_manager.__aexit__(None, None, None)
        _saver = None
        _context_manager = None
