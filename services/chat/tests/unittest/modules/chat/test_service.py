import unittest
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

from agentic_shared.core.domain_errors import NotFoundError
from agentic_shared.domains.chat.roles import ChatMessageRole
from agentic_shared.domains.persistence.entities import ChatMessage, ChatSession

from agentic_chat.modules.chat.service import ChatService
from agentic_chat.modules.chat.streaming.session_title import DEFAULT_SESSION_TITLE


class TestChatService(unittest.IsolatedAsyncioTestCase):
    def _service(self) -> tuple[ChatService, dict[str, AsyncMock]]:
        sessions_read = AsyncMock()
        sessions_write = AsyncMock()
        messages_read = AsyncMock()
        messages_write = AsyncMock()
        service = ChatService(sessions_read, sessions_write, messages_read, messages_write)
        return service, {
            "sessions_read": sessions_read,
            "sessions_write": sessions_write,
            "messages_read": messages_read,
            "messages_write": messages_write,
        }

    async def test_list_sessions(self) -> None:
        # Arrange
        session = ChatSession(
            id=uuid.uuid4(),
            title="One",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        service, mocks = self._service()
        mocks["sessions_read"].list_ordered_by_updated_desc.return_value = [session]

        # Act
        result = await service.list_sessions()

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "One")

    async def test_create_session_default_title(self) -> None:
        # Arrange
        service, mocks = self._service()
        now = datetime.now(UTC)
        created = ChatSession(
            id=uuid.uuid4(),
            title=DEFAULT_SESSION_TITLE,
            created_at=now,
            updated_at=now,
        )
        mocks["sessions_write"].add.return_value = created

        # Act
        result = await service.create_session()

        # Assert
        self.assertEqual(result.title, DEFAULT_SESSION_TITLE)
        added = mocks["sessions_write"].add.await_args.args[0]
        self.assertEqual(added.title, DEFAULT_SESSION_TITLE)

    async def test_create_session_custom_title(self) -> None:
        # Arrange
        service, mocks = self._service()
        now = datetime.now(UTC)
        created = ChatSession(id=uuid.uuid4(), title="Custom", created_at=now, updated_at=now)
        mocks["sessions_write"].add.return_value = created

        # Act
        result = await service.create_session(title="Custom")

        # Assert
        self.assertEqual(result.title, "Custom")

    async def test_delete_session_success(self) -> None:
        # Arrange
        session_id = uuid.uuid4()
        service, mocks = self._service()
        mocks["sessions_read"].get_by_id.return_value = ChatSession(id=session_id, title="x")

        # Act
        await service.delete_session(session_id)

        # Assert
        mocks["sessions_write"].delete.assert_awaited_once_with(session_id)

    async def test_delete_session_not_found(self) -> None:
        # Arrange
        service, mocks = self._service()
        mocks["sessions_read"].get_by_id.return_value = None

        # Act / Assert
        with self.assertRaises(NotFoundError):
            await service.delete_session(uuid.uuid4())

    async def test_get_messages(self) -> None:
        # Arrange
        session_id = uuid.uuid4()
        msg = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role=ChatMessageRole.USER,
            content="hello",
            created_at=datetime.now(UTC),
        )
        service, mocks = self._service()
        mocks["messages_read"].list_for_session_ordered.return_value = [msg]

        # Act
        result = await service.get_messages(session_id)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].content, "hello")

    async def test_truncate_messages_success(self) -> None:
        # Arrange
        session_id = uuid.uuid4()
        message_id = uuid.uuid4()
        service, mocks = self._service()
        mocks["messages_write"].delete_from_inclusive.return_value = True
        mocks["sessions_read"].get_by_id.return_value = ChatSession(id=session_id, title="x")

        # Act
        await service.truncate_messages_from(session_id, message_id)

        # Assert
        delete = mocks["messages_write"].delete_from_inclusive
        delete.assert_awaited_once_with(session_id, message_id)
        mocks["sessions_write"].update.assert_awaited_once()

    async def test_truncate_messages_not_found(self) -> None:
        # Arrange
        service, mocks = self._service()
        mocks["messages_write"].delete_from_inclusive.return_value = False

        # Act / Assert
        with self.assertRaises(NotFoundError):
            await service.truncate_messages_from(uuid.uuid4(), uuid.uuid4())


if __name__ == "__main__":
    unittest.main()
