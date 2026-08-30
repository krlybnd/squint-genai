import logging
import uuid
from datetime import UTC, datetime

from agentic_shared.domains.domain_errors import NotFoundError
from agentic_shared.domains.persistence.entities import ChatSession
from agentic_shared.domains.persistence.protocols.chat import (
    ChatMessageReadRepository,
    ChatMessageWriteRepository,
    ChatSessionReadRepository,
    ChatSessionWriteRepository,
)

from agentic_chat.modules.chat.schemas import ChatMessageOut, ChatSessionOut
from agentic_chat.modules.chat.streaming.session_title import DEFAULT_SESSION_TITLE

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        sessions_read: ChatSessionReadRepository,
        sessions_write: ChatSessionWriteRepository,
        messages_read: ChatMessageReadRepository,
        messages_write: ChatMessageWriteRepository,
    ) -> None:
        self._sessions_read = sessions_read
        self._sessions_write = sessions_write
        self._messages_read = messages_read
        self._messages_write = messages_write

    async def list_sessions(self) -> list[ChatSessionOut]:
        rows = await self._sessions_read.list_ordered_by_updated_desc()
        return [ChatSessionOut.model_validate(s) for s in rows]

    async def create_session(self, title: str | None = None) -> ChatSessionOut:
        session = ChatSession(title=title or DEFAULT_SESSION_TITLE)
        session = await self._sessions_write.add(session)
        logger.info("created session session_id=%s", session.id)
        return ChatSessionOut.model_validate(session)

    async def delete_session(self, session_id: uuid.UUID) -> None:
        chat_session = await self._sessions_read.get_by_id(session_id)
        if not chat_session:
            raise NotFoundError("Session not found")
        await self._sessions_write.delete(session_id)
        logger.info("deleted session session_id=%s", session_id)

    async def truncate_messages_from(self, session_id: uuid.UUID, message_id: uuid.UUID) -> None:
        deleted = await self._messages_write.delete_from_inclusive(session_id, message_id)
        if not deleted:
            raise NotFoundError("Message not found")
        chat_session = await self._sessions_read.get_by_id(session_id)
        if chat_session:
            chat_session.updated_at = datetime.now(UTC)
            await self._sessions_write.update(chat_session)
        logger.info(
            "truncated messages session_id=%s from_message_id=%s",
            session_id,
            message_id,
        )

    async def get_messages(self, session_id: uuid.UUID) -> list[ChatMessageOut]:
        rows = await self._messages_read.list_for_session_ordered(session_id)
        return [ChatMessageOut.from_entity(m) for m in rows]
