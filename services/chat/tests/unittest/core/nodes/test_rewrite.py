import unittest
from unittest.mock import AsyncMock

from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
from agentic_shared.domains.retrieval.models import IndexedDocumentEntry
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings

from agentic_chat.core.deps import AgentGraphDeps
from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.nodes.rewrite.node import RewriteQueryNode, _parse_rewrite_response
from agentic_chat.core.nodes.rewrite.prompt import build_rewrite_router_system_prompt


class TestRewriteQueryNode(unittest.IsolatedAsyncioTestCase):
    def _node(self) -> tuple[RewriteQueryNode, AsyncMock, AsyncMock]:
        retrieval = AsyncMock()
        chat_client = AsyncMock()
        query_pii = AsyncMock()
        query_pii.enabled = False
        deps = AgentGraphDeps(
            chat_client=chat_client,
            retrieval=retrieval,
            qdrant_top_k=5,
            guard=AsyncMock(),
            analyzer=AsyncMock(),
            anonymizer=AsyncMock(),
            query_pii=query_pii,
            pii_vault=PiiVaultSettings(_env_file=None),
        )
        return RewriteQueryNode(deps), retrieval, chat_client

    def test_parse_json_from_markdown_fence(self) -> None:
        # Arrange
        content = (
            '```json\n{"needs_document_search": true, "search_query": "q", "reason": "r"}\n```'
        )

        # Act
        parsed = _parse_rewrite_response(content)

        # Assert
        self.assertTrue(parsed.needs_document_search)
        self.assertEqual(parsed.search_query, "q")
        self.assertEqual(parsed.rewrite_reason, "r")

    async def test_success_needs_retrieval_with_search_query(self) -> None:
        # Arrange
        node, retrieval, chat_client = self._node()
        retrieval.list_indexed_documents.return_value = [
            IndexedDocumentEntry(doc_id="d1", source_file="a.pdf", chunk_count=3),
        ]
        chat_client.chat_completion.return_value = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"needs_document_search": true, "search_query": "pdf topic",'
                            ' "reason": "docs match"}'
                        ),
                    },
                },
            ],
        }

        # Act
        update = await node({"query": "what is in the pdf?", "tenant_id": "t1", "locale": "en"})

        # Assert
        self.assertTrue(update["needs_retrieval"])
        self.assertEqual(update["search_query"], "what is in the pdf?")
        self.assertEqual(update["indexed_document_count"], 1)
        kwargs = chat_client.chat_completion.await_args.kwargs
        self.assertEqual(kwargs["model"], LiteLLMChatSettings().litellm_router_model)

    async def test_success_needs_retrieval_false(self) -> None:
        # Arrange
        node, retrieval, chat_client = self._node()
        retrieval.list_indexed_documents.return_value = []
        chat_client.chat_completion.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"needs_document_search": false, "reason": "greeting"}',
                    },
                },
            ],
        }

        # Act
        update = await node({"query": "hello", "locale": "en"})

        # Assert
        self.assertFalse(update["needs_retrieval"])
        self.assertEqual(update["search_query"], "")
        self.assertIn("greeting", update["rewrite_reason"])

    async def test_search_uses_original_user_query(self) -> None:
        # Arrange
        node, retrieval, chat_client = self._node()
        retrieval.list_indexed_documents.return_value = []
        chat_client.chat_completion.return_value = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"needs_document_search": true, "search_query": "", "reason": ""}'
                        ),
                    },
                },
            ],
        }

        # Act
        update = await node({"query": "user question", "locale": "en"})

        # Assert
        self.assertTrue(update["needs_retrieval"])
        self.assertEqual(update["search_query"], "user question")

    async def test_search_keeps_original_query_when_safe_query_is_tokenized(self) -> None:
        node, retrieval, chat_client = self._node()
        retrieval.list_indexed_documents.return_value = []
        chat_client.chat_completion.return_value = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"needs_document_search": true, "search_query": "", "reason": ""}'
                        ),
                    },
                },
            ],
        }

        update = await node(
            {
                "query": "kicsoda Dr. Varga Levente?",
                "safe_query": "kicsoda Dr. <PERSON_A870C779> Levente?",
                "locale": "en",
            }
        )

        self.assertEqual(update["search_query"], "kicsoda Dr. Varga Levente?")

    async def test_llm_error_uses_fallback(self) -> None:
        # Arrange
        node, retrieval, chat_client = self._node()
        retrieval.list_indexed_documents.return_value = [
            IndexedDocumentEntry(doc_id="d1", source_file="b.pdf", chunk_count=1),
        ]
        chat_client.chat_completion.side_effect = RuntimeError("llm down")

        # Act
        update = await node({"query": "broken", "locale": "en"})

        # Assert
        self.assertTrue(update["needs_retrieval"])
        self.assertEqual(update["search_query"], "broken")
        self.assertEqual(update["indexed_document_count"], 1)

    def test_node_id(self) -> None:
        # Arrange
        node, _, _ = self._node()

        # Act / Assert
        self.assertIs(node.node_id, AgentGraphNode.REWRITE)

    def test_router_prompt_classifies_without_rewriting(self) -> None:
        # Arrange
        indexed = [
            IndexedDocumentEntry(doc_id="d1", source_file="paper.pdf", chunk_count=2),
        ]

        # Act
        prompt = build_rewrite_router_system_prompt(indexed=indexed)

        # Assert
        self.assertIn("user's original message", prompt)
        self.assertIn("Do not rewrite, translate, or keyword-ize", prompt)
        self.assertIn("parametric knowledge", prompt)


if __name__ == "__main__":
    unittest.main()
