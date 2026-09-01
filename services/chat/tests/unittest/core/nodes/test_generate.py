import asyncio
import unittest
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings

from agentic_chat.core.deps import AgentGraphDeps
from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.nodes.generate.node import GenerateNode
from agentic_chat.core.nodes.generate.settings import get_module_settings


def _text_stream(*parts: str) -> AsyncIterator[str]:
    async def _gen() -> AsyncIterator[str]:
        for part in parts:
            yield part

    return _gen()


class TestGenerateNode(unittest.IsolatedAsyncioTestCase):
    def _node(self) -> tuple[GenerateNode, MagicMock]:
        chat_client = MagicMock()
        chat_client.chat_completion = AsyncMock()
        chat_client.stream_chat_completion = MagicMock(return_value=_text_stream(""))

        async def _analyze(text: str, *, language: str = "en"):
            return []

        analyzer = AsyncMock()
        analyzer.analyze.side_effect = _analyze
        query_pii = AsyncMock()
        query_pii.enabled = False
        deps = AgentGraphDeps(
            chat_client=chat_client,
            retrieval=MagicMock(),
            qdrant_top_k=5,
            guard=AsyncMock(),
            analyzer=analyzer,
            anonymizer=AsyncMock(),
            query_pii=query_pii,
            pii_vault=PiiVaultSettings(_env_file=None, enabled=False),
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
        chat_client.stream_chat_completion = MagicMock(
            side_effect=lambda *_args, **_kwargs: _text_stream("The answer is 42."),
        )
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
        chat_client.chat_completion.assert_not_called()
        kwargs = chat_client.stream_chat_completion.call_args.kwargs
        self.assertEqual(kwargs["model"], LiteLLMChatSettings().litellm_model)

    async def test_success_no_citations_without_chunks(self) -> None:
        # Arrange
        node, chat_client = self._node()
        chat_client.stream_chat_completion = MagicMock(
            side_effect=lambda *_args, **_kwargs: _text_stream("Hi there!"),
        )

        # Act
        update = await node({"query": "hello", "retrieved_chunks": [], "locale": "en"})

        # Assert
        self.assertEqual(update["answer"], "Hi there!")
        self.assertEqual(update["citations"], [])
        chat_client.chat_completion.assert_not_called()

    async def test_llm_error_returns_localized_fallback(self) -> None:
        # Arrange
        node, chat_client = self._node()
        chat_client.stream_chat_completion = MagicMock(side_effect=RuntimeError("timeout"))

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
        self.assertTrue(node.streams_tokens())

    def test_default_prompts_answer_only_from_indexed_context(self) -> None:
        # Arrange / Act
        module = get_module_settings()
        rag = module.rag_system_prompt.lower()
        no_context = module.no_context_system_prompt.lower()

        # Assert — RAG must not fall back to parametric knowledge or upload CTAs
        self.assertIn("only", rag)
        self.assertIn("cannot find it in the indexed excerpts", rag)
        self.assertIn("copy numbers", rag)
        self.assertIn("vault placeholder", rag)
        self.assertIn("same placeholder", rag)
        self.assertIn("results table", rag)
        self.assertIn("one to three sentences", rag)
        self.assertIn("criminal classification", rag)
        self.assertIn("ordinary identifiers", rag)
        self.assertIn("do not appear", rag)
        self.assertIn("plain prose", rag)
        self.assertIn("latex", rag)
        self.assertIn("do not add offers to upload documents", rag)
        self.assertNotIn("answer directly if you can", no_context)
        self.assertIn("no matching indexed excerpts were found", no_context)
        self.assertIn("do not answer from", no_context)
        self.assertIn("memory or general knowledge", no_context)
        self.assertEqual(module.llm_temperature, 0.0)

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

        def fake_stream(messages: list[dict[str, str]], **_: object) -> AsyncIterator[str]:
            body = messages[1]["content"]
            text = "answer-a" if "q-a" in body else "answer-b"
            return _text_stream(text)

        chat_client.stream_chat_completion = MagicMock(side_effect=fake_stream)

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
