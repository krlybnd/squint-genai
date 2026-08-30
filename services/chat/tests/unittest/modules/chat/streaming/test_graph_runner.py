import json
import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock

from agentic_shared.domains.pii_vault.reveal_service import VaultRevealService
from agentic_shared.domains.pii_vault.settings import PiiVaultSettings

from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.modules.chat.enums import SseEventType
from agentic_chat.modules.chat.streaming.graph_runner import ChatGraphRunner
from agentic_chat.modules.chat.streaming.sse_events import parse_sse_chunk


async def _collect(aiter):
    return [item async for item in aiter]


class TestChatGraphRunner(unittest.IsolatedAsyncioTestCase):
    def _runner(
        self,
        *,
        vault_reveal: VaultRevealService | None = None,
        pii_vault: PiiVaultSettings | None = None,
    ) -> tuple[ChatGraphRunner, AsyncMock, AsyncMock]:
        graph = AsyncMock()
        messages_write = AsyncMock()
        return (
            ChatGraphRunner(
                graph,
                messages_write,
                vault_reveal=vault_reveal,
                pii_vault=pii_vault,
            ),
            graph,
            messages_write,
        )

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
            self.assertEqual(stream_mode, ["updates", "custom"])
            yield (
                "updates",
                {AgentGraphNode.GUARD.value: {"guard_blocked": False, "pii_redactions": 0}},
            )
            yield ("updates", {AgentGraphNode.GENERATE.value: {"answer": "done", "citations": []}})

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

    async def test_generate_does_not_slice_finished_answer(self) -> None:
        # Arrange
        runner, graph, messages_write = self._runner()
        session_id = uuid.uuid4()

        async def astream(_input, config=None, stream_mode=None):
            yield (
                "updates",
                {AgentGraphNode.GENERATE.value: {"answer": "hello world", "citations": []}},
            )

        graph.astream = astream
        graph.aget_state = AsyncMock(return_value=MagicMock(config={"configurable": {}}))

        # Act
        events = await _collect(runner.stream_execute(session_id, {}, input_state={"query": "hi"}))

        # Assert
        types = [parse_sse_chunk(e)["event"] for e in events]
        self.assertNotIn(SseEventType.TOKEN.value, types)
        self.assertIn(SseEventType.DONE.value, types)
        messages_write.add.assert_awaited_once()

    async def test_custom_stream_payloads_become_sse_tokens(self) -> None:
        # Arrange
        runner, graph, messages_write = self._runner()
        session_id = uuid.uuid4()

        async def astream(_input, config=None, stream_mode=None):
            yield ("custom", "hello ")
            yield ("custom", "world")
            yield (
                "updates",
                {AgentGraphNode.GENERATE.value: {"answer": "hello world", "citations": []}},
            )

        graph.astream = astream
        graph.aget_state = AsyncMock(return_value=MagicMock(config={"configurable": {}}))

        # Act
        events = await _collect(runner.stream_execute(session_id, {}, input_state={"query": "hi"}))

        # Assert
        types = [parse_sse_chunk(e)["event"] for e in events]
        self.assertIn(SseEventType.TOKEN.value, types)
        self.assertIn(SseEventType.DONE.value, types)
        messages_write.add.assert_awaited_once()

    async def test_custom_tokens_preserve_punctuation_and_newlines(self) -> None:
        # Arrange
        runner, graph, _ = self._runner()
        session_id = uuid.uuid4()
        answer = "it's a & b\nnext"

        async def astream(_input, config=None, stream_mode=None):
            yield ("custom", "it's a ")
            yield ("custom", "& b\nnext")
            yield ("updates", {AgentGraphNode.GENERATE.value: {"answer": answer, "citations": []}})

        graph.astream = astream
        graph.aget_state = AsyncMock(return_value=MagicMock(config={"configurable": {}}))

        # Act
        events = await _collect(runner.stream_execute(session_id, {}, input_state={"query": "hi"}))

        # Assert
        pieces = [
            json.loads(parse_sse_chunk(event)["data"])["content"]
            for event in events
            if parse_sse_chunk(event)["event"] == SseEventType.TOKEN.value
        ]
        self.assertEqual("".join(pieces), answer)

    async def test_stream_tokens_are_detokenized_when_vault_enabled(self) -> None:
        class _FakeVault:
            async def resolve_tokens(self, tokens):
                from agentic_shared.core.settings.secrets import SecuredStr

                return {"<PERSON_AABBCCDD>": SecuredStr("Jane VaultTest")}

        vault_reveal = VaultRevealService(_FakeVault())
        pii_vault = PiiVaultSettings(_env_file=None, enabled=True, sse_detokenize_enabled=True)
        runner, graph, messages_write = self._runner(vault_reveal=vault_reveal, pii_vault=pii_vault)
        session_id = uuid.uuid4()
        tokenized_answer = "Contact <PERSON_AABBCCDD> today."

        async def astream(_input, config=None, stream_mode=None):
            yield ("custom", "Contact <PERSON_AABB")
            yield ("custom", "CCDD> today.")
            yield (
                "updates",
                {AgentGraphNode.GENERATE.value: {"answer": tokenized_answer, "citations": []}},
            )

        graph.astream = astream
        graph.aget_state = AsyncMock(return_value=MagicMock(config={"configurable": {}}))

        events = await _collect(runner.stream_execute(session_id, {}, input_state={"query": "hi"}))

        token_pieces = [
            json.loads(parse_sse_chunk(event)["data"])["content"]
            for event in events
            if parse_sse_chunk(event)["event"] == SseEventType.TOKEN.value
        ]
        done = next(
            json.loads(parse_sse_chunk(event)["data"])
            for event in events
            if parse_sse_chunk(event)["event"] == SseEventType.DONE.value
        )
        self.assertEqual("".join(token_pieces), "Contact Jane VaultTest today.")
        self.assertEqual(done["answer"], "Contact Jane VaultTest today.")
        messages_write.add.assert_awaited_once()

    async def test_block_node_also_finishes_early(self) -> None:
        # Arrange
        runner, graph, messages_write = self._runner()
        session_id = uuid.uuid4()

        async def astream(_input, config=None, stream_mode=None):
            yield (
                "updates",
                {AgentGraphNode.BLOCK.value: {"answer": "blocked answer", "citations": []}},
            )

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
        types = [parse_sse_chunk(e)["event"] for e in events]
        self.assertNotIn(SseEventType.TOKEN.value, types)
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
            yield (
                "updates",
                {
                    AgentGraphNode.RETRIEVE.value: {
                        "answer": "final answer",
                        "retrieved_chunks": [],
                        "citations": [],
                    },
                },
            )

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
