from typing import Protocol, runtime_checkable
from uuid import UUID

from agentic_shared.domains.persistence.entities import ChatMessage, ChatSession
from agentic_shared.infrastructure.postgres.protocols import ReadRepository, WriteRepository


@runtime_checkable
class ChatSessionReadRepository(ReadRepository[ChatSession], Protocol):
    async def list_ordered_by_updated_desc(self, *, limit: int = 500) -> list[ChatSession]: ...


@runtime_checkable
class ChatSessionWriteRepository(WriteRepository[ChatSession], Protocol):
    pass


@runtime_checkable
class ChatMessageReadRepository(ReadRepository[ChatMessage], Protocol):
    async def list_for_session_ordered(self, session_id: UUID) -> list[ChatMessage]: ...


@runtime_checkable
class ChatMessageWriteRepository(WriteRepository[ChatMessage], Protocol):
    async def delete_last_assistant(self, session_id: UUID) -> bool: ...

    async def delete_from_inclusive(self, session_id: UUID, message_id: UUID) -> bool: ...
