from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from agentic_shared.domains.persistence.entities import ChatMessage, ChatSession
from agentic_shared.domains.persistence.limits import DEFAULT_LIST_LIMIT
from agentic_shared.infrastructure.postgres.repository import (
    SqlAlchemyReadRepository,
    SqlAlchemyWriteRepository,
)


class SqlAlchemyChatSessionReadRepository(SqlAlchemyReadRepository[ChatSession]):
    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        super().__init__(session, ChatSession, tenant_id)

    async def list_ordered_by_updated_desc(
        self, *, limit: int = DEFAULT_LIST_LIMIT
    ) -> list[ChatSession]:
        result = await self._session.execute(
            select(ChatSession)
            .where(ChatSession.tenant_id == self._tenant_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class SqlAlchemyChatSessionWriteRepository(SqlAlchemyWriteRepository[ChatSession]):
    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        super().__init__(session, ChatSession, tenant_id)

    async def delete(self, session_id: UUID) -> None:
        await self._session.execute(
            delete(ChatMessage).where(
                ChatMessage.session_id == session_id,
                ChatMessage.tenant_id == self._tenant_id,
            )
        )
        result = await self._session.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.tenant_id == self._tenant_id,
            )
        )
        chat_session = result.scalar_one_or_none()
        if chat_session:
            await self._session.delete(chat_session)
            await self._session.commit()


class SqlAlchemyChatMessageReadRepository(SqlAlchemyReadRepository[ChatMessage]):
    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        super().__init__(session, ChatMessage, tenant_id)

    async def list_for_session_ordered(self, session_id: UUID) -> list[ChatMessage]:
        result = await self._session.execute(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.tenant_id == self._tenant_id,
            )
            .order_by(ChatMessage.created_at)
        )
        return list(result.scalars().all())


class SqlAlchemyChatMessageWriteRepository(SqlAlchemyWriteRepository[ChatMessage]):
    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        super().__init__(session, ChatMessage, tenant_id)

    async def delete(self, entity_id: UUID) -> None:
        message = await self.get_by_id(entity_id)
        if message:
            await self._session.delete(message)
            await self._session.commit()

    async def delete_last_assistant(self, session_id: UUID) -> bool:
        result = await self._session.execute(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.role == "assistant",
                ChatMessage.tenant_id == self._tenant_id,
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        message = result.scalar_one_or_none()
        if not message:
            return False
        await self._session.delete(message)
        await self._session.commit()
        return True

    async def delete_from_inclusive(self, session_id: UUID, message_id: UUID) -> bool:
        anchor = await self.get_by_id(message_id)
        if anchor is None or anchor.session_id != session_id:
            return False
        result = await self._session.execute(
            select(ChatMessage).where(
                ChatMessage.session_id == session_id,
                ChatMessage.tenant_id == self._tenant_id,
                ChatMessage.created_at >= anchor.created_at,
            )
        )
        messages = list(result.scalars().all())
        if not messages:
            return False
        for message in messages:
            await self._session.delete(message)
        await self._session.commit()
        return True
