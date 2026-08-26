import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock

from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.modules.chat.enums import SseEventType
from agentic_chat.modules.chat.streaming.graph_runner import ChatGraphRunner
from agentic_chat.modules.chat.streaming.sse_events import parse_sse_chunk


async def _collect(aiter):
    return [item async for item in aiter]


class TestChatGraphRunner(unittest.IsolatedAsyncioTestCase):
    def _runner(self) -> tuple[ChatGraphRunner, AsyncMock, AsyncMock]:
        graph = AsyncMock()
        messages_write = AsyncMock()
        return ChatGraphRunner(graph, messages_write), graph, messages_write

    async def test_find_start_checkpoint(self) -> None:
        # Arrange
        runner, graph, _ = self._runner()
        start_state = MagicMock()
        start_state.next = ("__start__",)
        start_state.config = {"configurable": {"checkpoint_id": "cp-start"}}
        other_state = MagicMock()
        other_state.next = ("guard",)
        other_state.config = {"configurable": {"checkpoint_id": "cp-other"}}

        async def history(_config):
            for state in (other_state, start_state):
                yield state

        graph.aget_state_history = history

        # Act
        result = await runner.find_start_checkpoint({})

        # Assert
        self.assertEqual(result, "cp-start")

    async def test_stream_includes_checkpoint_on_reasoning(self) -> None:
        # Arrange
        runner, graph, _ = self._runner()
        session_id = uuid.uuid4()

        async def astream(_input, config=None, stream_mode=None):
            yield {AgentGraphNode.GUARD.value: {"guard_blocked": False, "pii_redactions": 0}}
            yield {AgentGraphNode.GENERATE.value: {"answer": "done", "citations": []}}

        graph.astream = astream
        graph.aget_state = AsyncMock(
            return_value=MagicMock(config={"configurable": {"checkpoint_id": "cp-1"}}),
        )

        # Act
        events = await _collect(runner.stream_execute(session_id, {}, input_state={"query": "hi"}))

        # Assert
        reasoning = [
            parse_sse_chunk(e)
            for e in events
            if parse_sse_chunk(e)["event"] == SseEventType.REASONING.value
        ]
        self.assertTrue(any('"checkpoint_id": "cp-1"' in r["data"] for r in reasoning))

    async def test_early_return_streams_tokens_on_generate(self) -> None:
        # Arrange
        runner, graph, messages_write = self._runner()
        session_id = uuid.uuid4()

        async def astream(_input, config=None, stream_mode=None):
            yield {AgentGraphNode.GENERATE.value: {"answer": "hello world", "citations": []}}

        graph.astream = astream
        graph.aget_state = AsyncMock(return_value=MagicMock(config={"configurable": {}}))

        # Act
        events = await _collect(runner.stream_execute(session_id, {}, input_state={"query": "hi"}))

        # Assert
        types = [parse_sse_chunk(e)["event"] for e in events]
        self.assertIn(SseEventType.TOKEN.value, types)
        self.assertIn(SseEventType.DONE.value, types)
        messages_write.add.assert_awaited_once()

    async def test_block_node_also_finishes_early(self) -> None:
        # Arrange
        runner, graph, messages_write = self._runner()
        session_id = uuid.uuid4()

        async def astream(_input, config=None, stream_mode=None):
            yield {AgentGraphNode.BLOCK.value: {"answer": "blocked answer", "citations": []}}

        graph.astream = astream
        graph.aget_state = AsyncMock(return_value=MagicMock(config={"configurable": {}}))

        # Act
        events = await _collect(runner.stream_execute(session_id, {}, input_state={"query": "bad"}))

        # Assert
        done_events = [
            parse_sse_chunk(e)
            for e in events
            if parse_sse_chunk(e)["event"] == SseEventType.DONE.value
        ]
        self.assertEqual(len(done_events), 1)
        self.assertIn("blocked answer", done_events[0]["data"])
        messages_write.add.assert_awaited_once()

    async def test_graph_error_yields_error_event(self) -> None:
        # Arrange
        runner, graph, _ = self._runner()
        session_id = uuid.uuid4()

        async def astream(_input, config=None, stream_mode=None):
            raise RuntimeError("graph blew up")
            yield {}  # pragma: no cover

        graph.astream = astream

        # Act
        events = await _collect(
            runner.stream_execute(session_id, {}, input_state={"query": "x", "locale": "en"}),
        )

        # Assert
        self.assertEqual(parse_sse_chunk(events[-1])["event"], SseEventType.ERROR.value)
        self.assertIn("graph blew up", parse_sse_chunk(events[-1])["data"])

    async def test_fallback_finish_without_early_return(self) -> None:
        # Arrange
        runner, graph, messages_write = self._runner()
        session_id = uuid.uuid4()

        async def astream(_input, config=None, stream_mode=None):
            yield {
                AgentGraphNode.RETRIEVE.value: {
                    "answer": "final answer",
                    "retrieved_chunks": [],
                    "citations": [],
                },
            }

        graph.astream = astream
        graph.aget_state = AsyncMock(return_value=MagicMock(config={"configurable": {}}))

        # Act
        events = await _collect(
            runner.stream_execute(
                session_id,
                {},
                input_state={"query": "hi", "messages": [{"role": "user", "content": "hi"}]},
            ),
        )

        # Assert
        types = [parse_sse_chunk(e)["event"] for e in events]
        self.assertNotIn(SseEventType.TOKEN.value, types)
        self.assertIn(SseEventType.DONE.value, types)
        messages_write.add.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
