import unittest
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from agentic_shared.domains.chat.roles import ChatMessageRole
from agentic_shared.domains.persistence.entities import ChatMessage, ChatSession

from agentic_chat.modules.chat.enums import SseEventType
from agentic_chat.modules.chat.streaming.session_title import DEFAULT_SESSION_TITLE
from agentic_chat.modules.chat.streaming.sse_events import parse_sse_chunk
from agentic_chat.modules.chat.streaming.stream_service import ChatStreamService, _thread_id


async def _collect(aiter):
    return [item async for item in aiter]


class _StreamExecuteMock:
    def __init__(self, events: list[str] | None = None) -> None:
        self._events = events or ['event: done\ndata: {"answer": "ok"}\n\n']
        self.calls: list[tuple[tuple, dict]] = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))

        async def _gen():
            for event in self._events:
                yield event

        return _gen()


class TestChatStreamService(unittest.IsolatedAsyncioTestCase):
    def _service(
        self,
        *,
        session: ChatSession | None = None,
        messages: list[ChatMessage] | None = None,
        graph_events: list[str] | None = None,
        query_pii=None,
        vault_reveal=None,
        analyzer=None,
        anonymizer=None,
    ) -> tuple[ChatStreamService, dict[str, AsyncMock | _StreamExecuteMock]]:
        sessions_read = AsyncMock()
        sessions_write = AsyncMock()
        messages_read = AsyncMock()
        messages_write = AsyncMock()
        stream_execute = _StreamExecuteMock(graph_events)
        graph_runner = MagicMock()
        title_generator = AsyncMock()

        sessions_read.get_by_id.return_value = session
        messages_read.list_for_session_ordered.return_value = messages or []
        title_generator.generate.return_value = "Generated title"

        graph_runner.stream_execute = stream_execute
        graph_runner.find_start_checkpoint = AsyncMock(return_value="cp-replay")

        service = ChatStreamService(
            sessions_read=sessions_read,
            sessions_write=sessions_write,
            messages_read=messages_read,
            messages_write=messages_write,
            graph_runner=graph_runner,
            title_generator=title_generator,
            tenant_id="tenant-1",
            query_pii=query_pii,
            vault_reveal=vault_reveal,
            analyzer=analyzer,
            anonymizer=anonymizer,
        )
        mocks = {
            "sessions_read": sessions_read,
            "sessions_write": sessions_write,
            "messages_read": messages_read,
            "messages_write": messages_write,
            "graph_runner": graph_runner,
            "stream_execute": stream_execute,
            "title_generator": title_generator,
        }
        return service, mocks

    def test_thread_id_format(self) -> None:
        # Arrange
        session_id = uuid.uuid4()
        expected = f"tenant-1:{session_id}:run-abc"

        # Act / Assert
        self.assertEqual(_thread_id("tenant-1", session_id, "run-abc"), expected)

    async def test_stream_response_event_order_first_turn(self) -> None:
        # Arrange
        session_id = uuid.uuid4()
        session = ChatSession(id=session_id, title=DEFAULT_SESSION_TITLE)
        user_msg = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role=ChatMessageRole.USER,
            content="hello world",
            created_at=datetime.now(UTC),
        )
        service, mocks = self._service(session=session, messages=[user_msg], graph_events=[])

        # Act
        events = await _collect(service.stream_response(session_id, "hello world", run_id="run-1"))

        # Assert
        types = [parse_sse_chunk(e)["event"] for e in events]
        self.assertEqual(types[0], SseEventType.RUN.value)
        self.assertEqual(types[1], SseEventType.REASONING.value)
        self.assertIn(SseEventType.SESSION.value, types)
        mocks["messages_write"].add.assert_awaited()
        mocks["title_generator"].generate.assert_awaited_once()

    async def test_title_llm_receives_tokenized_prompt_when_vault_enabled(self) -> None:
        session_id = uuid.uuid4()
        session = ChatSession(id=session_id, title=DEFAULT_SESSION_TITLE)
        user_msg = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role=ChatMessageRole.USER,
            content="Ask about Jane VaultTest salary",
            created_at=datetime.now(UTC),
        )
        query_pii = AsyncMock()
        query_pii.enabled = True
        query_pii.tokenize_query.return_value = "Ask about <PERSON_AABBCCDD> salary"
        vault_reveal = AsyncMock()
        vault_reveal.reveal_text.return_value = "Ask about Jane VaultTest salary"
        service, mocks = self._service(
            session=session,
            messages=[user_msg],
            graph_events=[],
            query_pii=query_pii,
            vault_reveal=vault_reveal,
        )

        await _collect(
            service.stream_response(session_id, "Ask about Jane VaultTest salary", run_id="run-1"),
        )

        query_pii.tokenize_query.assert_awaited_once_with(
            "Ask about Jane VaultTest salary",
            tenant_id="tenant-1",
        )
        mocks["title_generator"].generate.assert_awaited_once()
        prompt = mocks["title_generator"].generate.await_args.args[0]
        self.assertEqual(prompt, "Ask about <PERSON_AABBCCDD> salary")
        self.assertNotIn("Jane VaultTest", prompt)
        vault_reveal.reveal_text.assert_awaited_once()
        self.assertEqual(session.title, "Ask about Jane VaultTest salary")

    async def test_title_llm_skipped_when_sanitization_fails(self) -> None:
        session_id = uuid.uuid4()
        session = ChatSession(id=session_id, title=DEFAULT_SESSION_TITLE)
        user_msg = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role=ChatMessageRole.USER,
            content="secret name",
            created_at=datetime.now(UTC),
        )
        query_pii = AsyncMock()
        query_pii.enabled = True
        query_pii.tokenize_query.side_effect = RuntimeError("analyzer down")
        service, mocks = self._service(
            session=session,
            messages=[user_msg],
            graph_events=[],
            query_pii=query_pii,
        )

        await _collect(service.stream_response(session_id, "secret name", run_id="run-1"))

        mocks["title_generator"].generate.assert_not_called()
        self.assertEqual(session.title, "secret name")

    async def test_title_llm_receives_masked_prompt_when_vault_disabled(self) -> None:
        session_id = uuid.uuid4()
        session = ChatSession(id=session_id, title=DEFAULT_SESSION_TITLE)
        user_msg = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role=ChatMessageRole.USER,
            content="Call Jane at jane@example.com",
            created_at=datetime.now(UTC),
        )
        analyzer = AsyncMock()
        analyzer.analyze.return_value = [
            MagicMock(entity_type="EMAIL_ADDRESS", start=14, end=30),
        ]
        anonymizer = AsyncMock()
        anonymizer.anonymize.return_value = MagicMock(text="Call Jane at <EMAIL_ADDRESS>")
        service, mocks = self._service(
            session=session,
            messages=[user_msg],
            graph_events=[],
            analyzer=analyzer,
            anonymizer=anonymizer,
        )

        await _collect(
            service.stream_response(session_id, "Call Jane at jane@example.com", run_id="run-1"),
        )

        mocks["title_generator"].generate.assert_awaited_once()
        prompt = mocks["title_generator"].generate.await_args.args[0]
        self.assertEqual(prompt, "Call Jane at <EMAIL_ADDRESS>")
        self.assertNotIn("jane@example.com", prompt)

    async def test_stream_response_skips_title_on_subsequent_turn(self) -> None:
        # Arrange
        session_id = uuid.uuid4()
        session = ChatSession(id=session_id, title="Existing title")
        prior = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role=ChatMessageRole.USER,
            content="first",
            created_at=datetime.now(UTC),
        )
        service, mocks = self._service(session=session, messages=[prior])

        # Act
        events = await _collect(service.stream_response(session_id, "second message"))

        # Assert
        title_steps = [
            parse_sse_chunk(e)["data"]
            for e in events
            if parse_sse_chunk(e)["event"] == SseEventType.REASONING.value
            and '"step": "title"' in parse_sse_chunk(e)["data"]
        ]
        self.assertEqual(title_steps, [])
        mocks["title_generator"].generate.assert_not_called()

    async def test_stream_response_session_not_found(self) -> None:
        # Arrange
        service, _ = self._service(session=None)

        # Act
        events = await _collect(service.stream_response(uuid.uuid4(), "hi"))

        # Assert
        self.assertEqual(parse_sse_chunk(events[0])["event"], SseEventType.ERROR.value)

    async def test_stream_replay_resolves_checkpoint_and_yields_events(self) -> None:
        # Arrange
        session_id = uuid.uuid4()
        session = ChatSession(id=session_id, title="Replay session")
        service, mocks = self._service(
            session=session,
            graph_events=['event: done\ndata: {"answer": "replayed"}\n\n'],
        )

        # Act
        events = await _collect(
            service.stream_replay(session_id, "run-99", "original query", locale="en"),
        )

        # Assert
        types = [parse_sse_chunk(e)["event"] for e in events]
        self.assertEqual(types[0], SseEventType.RUN.value)
        self.assertIn(SseEventType.REASONING.value, types)
        mocks["graph_runner"].find_start_checkpoint.assert_awaited_once()
        mocks["messages_write"].delete_last_assistant.assert_awaited_once_with(session_id)

    async def test_stream_replay_no_checkpoint(self) -> None:
        # Arrange
        session_id = uuid.uuid4()
        session = ChatSession(id=session_id, title="Replay session")
        service, mocks = self._service(session=session)
        mocks["graph_runner"].find_start_checkpoint = AsyncMock(return_value=None)

        # Act
        events = await _collect(service.stream_replay(session_id, "run-99", "q"))

        # Assert
        self.assertEqual(parse_sse_chunk(events[0])["event"], SseEventType.ERROR.value)

    async def test_stream_replay_uses_provided_checkpoint(self) -> None:
        # Arrange
        session_id = uuid.uuid4()
        session = ChatSession(id=session_id, title="Replay session")
        service, mocks = self._service(session=session)

        # Act
        await _collect(
            service.stream_replay(session_id, "run-99", "q", checkpoint_id="cp-fixed"),
        )

        # Assert
        mocks["graph_runner"].find_start_checkpoint.assert_not_called()
        call_args = mocks["stream_execute"].calls[0][0]
        config = call_args[1]
        self.assertEqual(config["configurable"]["checkpoint_id"], "cp-fixed")


if __name__ == "__main__":
    unittest.main()
