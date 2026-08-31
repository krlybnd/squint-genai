import unittest
from unittest.mock import AsyncMock, MagicMock

from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
from agentic_shared.domains.retrieval.models import (
    RetrievedChunk,
    SearchDocumentsResult,
    SearchMeta,
)

from agentic_chat.core.deps import AgentGraphDeps
from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.nodes.retrieve import RetrieveNode


class TestRetrieveNode(unittest.IsolatedAsyncioTestCase):
    def _node(self, *, top_k: int = 5) -> tuple[RetrieveNode, AsyncMock]:
        retrieval = AsyncMock()
        query_pii = AsyncMock()
        query_pii.enabled = False
        deps = AgentGraphDeps(
            chat_client=MagicMock(),
            retrieval=retrieval,
            qdrant_top_k=top_k,
            guard=AsyncMock(),
            analyzer=AsyncMock(),
            anonymizer=AsyncMock(),
            query_pii=query_pii,
            pii_vault=PiiVaultSettings(_env_file=None),
        )
        return RetrieveNode(deps), retrieval

    def test_node_id(self) -> None:
        # Arrange
        node, _ = self._node()

        # Act / Assert
        self.assertIs(node.node_id, AgentGraphNode.RETRIEVE)

    async def test_skips_when_needs_retrieval_false(self) -> None:
        # Arrange
        node, retrieval = self._node()

        # Act
        update = await node(
            {"needs_retrieval": False, "rewrite_reason": "no docs needed", "locale": "en"},
        )

        # Assert
        self.assertEqual(update["retrieved_chunks"], [])
        meta = update["search_meta"]
        self.assertTrue(meta["skipped"])
        self.assertEqual(meta["reason"], "no docs needed")
        retrieval.search_documents_with_meta.assert_not_called()

    async def test_skips_on_empty_search_query(self) -> None:
        # Arrange
        node, retrieval = self._node()

        # Act
        update = await node({"needs_retrieval": True, "search_query": "   ", "locale": "en"})

        # Assert
        self.assertEqual(update["retrieved_chunks"], [])
        self.assertTrue(update["search_meta"]["skipped"])
        retrieval.search_documents_with_meta.assert_not_called()

    async def test_searches_with_search_query(self) -> None:
        # Arrange
        node, retrieval = self._node(top_k=3)
        chunk = RetrievedChunk(
            chunk_id="c1",
            doc_id="d1",
            source_file="doc.pdf",
            page=1,
            text="hello world",
            score=0.9,
        )
        retrieval.search_documents_with_meta.return_value = SearchDocumentsResult(
            chunks=[chunk],
            meta=SearchMeta.hybrid_start(
                query="find info",
                dense_model="d",
                sparse_model="s",
                candidate_top_k=10,
                final_top_k=3,
            ),
        )

        # Act
        update = await node(
            {
                "needs_retrieval": True,
                "search_query": "find info",
                "tenant_id": "tenant-a",
                "locale": "en",
            },
        )

        # Assert
        retrieval.search_documents_with_meta.assert_awaited_once_with(
            "find info",
            top_k=3,
            tenant_id="tenant-a",
        )
        self.assertEqual(len(update["retrieved_chunks"]), 1)
        self.assertEqual(update["retrieved_chunks"][0]["chunk_id"], "c1")
        self.assertEqual(update["search_meta"]["search_query"], "find info")
        self.assertEqual(update["search_meta"]["results_count"], 1)

    async def test_prefers_original_query_over_tokenized_search_query(self) -> None:
        node, retrieval = self._node()
        retrieval.search_documents_with_meta.return_value = SearchDocumentsResult(
            chunks=[],
            meta=SearchMeta(),
        )

        await node(
            {
                "needs_retrieval": True,
                "query": "kicsoda Dr. Varga Levente?",
                "search_query": "kicsoda Dr. <PERSON_A870C779> Levente?",
                "locale": "en",
            },
        )

        retrieval.search_documents_with_meta.assert_awaited_once_with(
            "kicsoda Dr. Varga Levente?",
            top_k=5,
            tenant_id="default",
        )

    async def test_falls_back_to_query_when_search_query_missing(self) -> None:
        # Arrange
        node, retrieval = self._node()
        empty_result = SearchDocumentsResult(chunks=[], meta=SearchMeta())
        retrieval.search_documents_with_meta.return_value = empty_result

        # Act
        await node({"needs_retrieval": True, "query": "fallback q", "locale": "en"})

        # Assert
        retrieval.search_documents_with_meta.assert_awaited_once_with(
            "fallback q",
            top_k=5,
            tenant_id="default",
        )


if __name__ == "__main__":
    unittest.main()
