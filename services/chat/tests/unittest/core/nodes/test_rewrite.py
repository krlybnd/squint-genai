import unittest
from unittest.mock import AsyncMock

from agentic_shared.domains.retrieval.models import IndexedDocumentEntry

from agentic_chat.core.deps import AgentGraphDeps
from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.nodes.rewrite.node import RewriteQueryNode, _parse_rewrite_response


class TestRewriteQueryNode(unittest.IsolatedAsyncioTestCase):
    def _node(self) -> tuple[RewriteQueryNode, AsyncMock, AsyncMock]:
        retrieval = AsyncMock()
        chat_client = AsyncMock()
        deps = AgentGraphDeps(
            chat_client=chat_client,
            retrieval=retrieval,
            qdrant_top_k=5,
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
        self.assertEqual(update["search_query"], "pdf topic")
        self.assertEqual(update["indexed_document_count"], 1)

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

    async def test_search_query_falls_back_to_user_query(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
