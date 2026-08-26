import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from agentic_chat.core.deps import AgentGraphDeps
from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.nodes.generate.node import GenerateNode
from agentic_chat.core.nodes.generate.settings import get_module_settings


class TestGenerateNode(unittest.IsolatedAsyncioTestCase):
    def _node(self) -> tuple[GenerateNode, AsyncMock]:
        chat_client = AsyncMock()
        deps = AgentGraphDeps(
            chat_client=chat_client,
            retrieval=MagicMock(),
            qdrant_top_k=5,
        )
        return GenerateNode(deps), chat_client

    async def test_build_messages_no_context(self) -> None:
        # Arrange
        node, _ = self._node()

        # Act
        _, ctx = await node.prepare({"query": "hello", "locale": "en", "retrieved_chunks": []})
        messages = await node.build_messages({"query": "hello", "retrieved_chunks": []}, ctx)
        module = get_module_settings()

        # Assert
        self.assertEqual(messages[0]["content"], module.no_context_system_prompt)
        self.assertEqual(messages[1]["content"], "hello")

    async def test_build_messages_rag_with_chunks(self) -> None:
        # Arrange
        node, _ = self._node()
        chunks = [
            {
                "chunk_id": "c1",
                "doc_id": "d1",
                "source_file": "paper.pdf",
                "page": 2,
                "text": "Important fact about AI.",
            },
        ]
        state = {"query": "What is AI?", "retrieved_chunks": chunks, "locale": "en"}

        # Act
        _, ctx = await node.prepare(state)
        messages = await node.build_messages(state, ctx)
        module = get_module_settings()

        # Assert
        self.assertEqual(messages[0]["content"], module.rag_system_prompt)
        self.assertIn("paper.pdf", messages[1]["content"])
        self.assertIn("Important fact about AI.", messages[1]["content"])
        self.assertIn("What is AI?", messages[1]["content"])

    async def test_success_includes_citations_when_chunks_present(self) -> None:
        # Arrange
        node, chat_client = self._node()
        chat_client.chat_completion.return_value = {
            "choices": [{"message": {"content": "The answer is 42."}}],
        }
        chunks = [
            {
                "chunk_id": "c1",
                "doc_id": "d1",
                "source_file": "doc.pdf",
                "page": 1,
                "text": "source text",
            },
        ]

        # Act
        update = await node({"query": "question", "retrieved_chunks": chunks, "locale": "en"})

        # Assert
        self.assertEqual(update["answer"], "The answer is 42.")
        self.assertEqual(len(update["citations"]), 1)
        self.assertEqual(update["citations"][0]["chunk_id"], "c1")

    async def test_success_no_citations_without_chunks(self) -> None:
        # Arrange
        node, chat_client = self._node()
        chat_client.chat_completion.return_value = {
            "choices": [{"message": {"content": "Hi there!"}}],
        }

        # Act
        update = await node({"query": "hello", "retrieved_chunks": [], "locale": "en"})

        # Assert
        self.assertEqual(update["answer"], "Hi there!")
        self.assertEqual(update["citations"], [])

    async def test_llm_error_returns_localized_fallback(self) -> None:
        # Arrange
        node, chat_client = self._node()
        chat_client.chat_completion.side_effect = RuntimeError("timeout")

        # Act
        update = await node({"query": "fail", "retrieved_chunks": [], "locale": "en"})

        # Assert
        self.assertTrue(update["answer"])
        self.assertEqual(update["citations"], [])

    def test_node_id(self) -> None:
        # Arrange
        node, _ = self._node()

        # Act / Assert
        self.assertIs(node.node_id, AgentGraphNode.GENERATE)

    async def test_concurrent_calls_do_not_share_mutable_state(self) -> None:
        # Arrange — one APP-scoped node instance must serve concurrent requests safely.
        node, chat_client = self._node()
        chunks_a = [
            {
                "chunk_id": "c-a",
                "doc_id": "d1",
                "source_file": "a.pdf",
                "page": 1,
                "text": "alpha",
            },
        ]

        async def fake_completion(messages: list[dict[str, str]], **_: object) -> dict[str, object]:
            body = messages[1]["content"]
            if "q-a" in body:
                return {"choices": [{"message": {"content": "answer-a"}}]}
            return {"choices": [{"message": {"content": "answer-b"}}]}

        chat_client.chat_completion = AsyncMock(side_effect=fake_completion)

        # Act
        update_a, update_b = await asyncio.gather(
            node({"query": "q-a", "retrieved_chunks": chunks_a, "locale": "en"}),
            node({"query": "q-b", "retrieved_chunks": [], "locale": "en"}),
        )

        # Assert
        self.assertEqual(update_a["answer"], "answer-a")
        self.assertEqual(update_a["citations"][0]["chunk_id"], "c-a")
        self.assertEqual(update_b["answer"], "answer-b")
        self.assertEqual(update_b["citations"], [])


if __name__ == "__main__":
    unittest.main()
