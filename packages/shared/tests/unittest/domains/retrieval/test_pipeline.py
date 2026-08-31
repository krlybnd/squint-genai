import unittest
from unittest.mock import patch

from qdrant_client.http.models import SparseVector

from agentic_shared.domains.retrieval.models import RetrievedChunk
from agentic_shared.domains.retrieval.service import AsyncRetrievalService, RetrievalService
from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings
from agentic_shared.integrations.litellm.rerank.errors import RerankError
from agentic_shared.integrations.litellm.rerank.models import RerankHit


class _StubChunkReadRepository:
    default_top_k = 5
    candidate_top_k = 30
    sparse_model = "Qdrant/bm25"

    def get_by_id(self, point_id: str, *, tenant_id: str):
        _ = (point_id, tenant_id)
        return None

    def hybrid_search(self, *, tenant_id: str, dense_vector, sparse_vector, limit):
        _ = tenant_id
        return [
            RetrievedChunk(chunk_id="a", text="alpha chunk", score=0.9),
            RetrievedChunk(chunk_id="b", text="beta chunk", score=0.8),
            RetrievedChunk(chunk_id="c", text="gamma chunk", score=0.7),
        ][:limit]

    def scroll_document_catalog(self, *, tenant_id: str):
        _ = tenant_id
        return []

    def scroll_document_chunks(self, doc_id, *, tenant_id: str, limit=100, offset=None):
        _ = (doc_id, tenant_id)
        return [], None

    def scroll_source_file_chunks(self, source_file, *, tenant_id: str, limit=100, offset=None):
        _ = (source_file, tenant_id)
        return [], None


class TestRetrievalPipeline(unittest.TestCase):
    @patch("agentic_shared.domains.retrieval.service.embed_sparse_text")
    @patch("agentic_shared.domains.retrieval.service.embed_dense_text")
    def test_search_documents_returns_rrf_order(
        self,
        mock_dense,
        mock_sparse,
    ) -> None:
        # Arrange
        mock_dense.return_value = [0.1, 0.2]
        mock_sparse.return_value = SparseVector(indices=[1], values=[0.5])
        service = RetrievalService(
            _StubChunkReadRepository(),
            LiteLLMChatSettings(),
            LiteLLMEmbeddingSettings(),
        )

        # Act
        results = service.search_documents("query", top_k=2, tenant_id="default")

        # Assert
        self.assertEqual([item.chunk_id for item in results], ["a", "b"])

    @patch("agentic_shared.domains.retrieval.service.embed_sparse_text")
    @patch("agentic_shared.domains.retrieval.service.embed_dense_text")
    def test_search_documents_empty_query_returns_no_chunks(
        self,
        mock_dense,
        mock_sparse,
    ) -> None:
        # Arrange
        service = RetrievalService(
            _StubChunkReadRepository(),
            LiteLLMChatSettings(),
            LiteLLMEmbeddingSettings(),
        )

        # Act
        result = service.search_documents_with_meta("   ", tenant_id="default")

        # Assert
        self.assertEqual(result.chunks, [])
        mock_dense.assert_not_called()
        mock_sparse.assert_not_called()

    @patch("agentic_shared.domains.retrieval.service.embed_sparse_text")
    @patch("agentic_shared.domains.retrieval.service.embed_dense_text")
    def test_search_documents_single_candidate(
        self,
        mock_dense,
        mock_sparse,
    ) -> None:
        # Arrange
        mock_dense.return_value = [0.1]
        mock_sparse.return_value = SparseVector(indices=[1], values=[0.5])

        class _SingleHitReader(_StubChunkReadRepository):
            def hybrid_search(self, *, tenant_id: str, dense_vector, sparse_vector, limit):
                _ = (tenant_id, dense_vector, sparse_vector, limit)
                return [RetrievedChunk(chunk_id="only", text="solo", score=0.99)]

        service = RetrievalService(
            _SingleHitReader(),
            LiteLLMChatSettings(),
            LiteLLMEmbeddingSettings(),
        )

        # Act
        result = service.search_documents_with_meta("query", top_k=1, tenant_id="default")

        # Assert
        self.assertEqual([item.chunk_id for item in result.chunks], ["only"])

    @patch("agentic_shared.domains.retrieval.service.embed_sparse_text")
    @patch("agentic_shared.domains.retrieval.service.embed_dense_text")
    def test_search_documents_reranks_after_rrf(
        self,
        mock_dense,
        mock_sparse,
    ) -> None:
        mock_dense.return_value = [0.1, 0.2]
        mock_sparse.return_value = SparseVector(indices=[1], values=[0.5])

        class _Reranker:
            enabled = True
            model = "rerank"

            async def rerank(self, query, documents, *, top_n):
                _ = (query, documents)
                return [RerankHit(index=2, score=0.99), RerankHit(index=0, score=0.1)][:top_n]

        service = RetrievalService(
            _StubChunkReadRepository(),
            LiteLLMChatSettings(),
            LiteLLMEmbeddingSettings(),
            reranker=_Reranker(),
        )

        result = service.search_documents_with_meta("query", top_k=2, tenant_id="default")

        self.assertEqual([item.chunk_id for item in result.chunks], ["c", "a"])
        self.assertTrue(result.meta.reranked)
        self.assertEqual(result.meta.rerank_model, "rerank")

    @patch("agentic_shared.domains.retrieval.service.embed_sparse_text")
    @patch("agentic_shared.domains.retrieval.service.embed_dense_text")
    def test_search_documents_rerank_error_keeps_rrf(
        self,
        mock_dense,
        mock_sparse,
    ) -> None:
        mock_dense.return_value = [0.1, 0.2]
        mock_sparse.return_value = SparseVector(indices=[1], values=[0.5])

        class _BrokenReranker:
            enabled = True
            model = "rerank"

            async def rerank(self, query, documents, *, top_n):
                _ = (query, documents, top_n)
                raise RerankError("tei down")

        service = RetrievalService(
            _StubChunkReadRepository(),
            LiteLLMChatSettings(),
            LiteLLMEmbeddingSettings(),
            reranker=_BrokenReranker(),
        )

        result = service.search_documents("query", top_k=2, tenant_id="default")

        self.assertEqual([item.chunk_id for item in result], ["a", "b"])


class TestRetrievalPipelineAsync(unittest.IsolatedAsyncioTestCase):
    @patch("agentic_shared.domains.retrieval.service.embed_sparse_text")
    @patch("agentic_shared.domains.retrieval.service.embed_dense_text")
    async def test_search_documents_async_returns_rrf_order(
        self,
        mock_dense,
        mock_sparse,
    ) -> None:
        # Arrange
        mock_dense.return_value = [0.1, 0.2]
        mock_sparse.return_value = SparseVector(indices=[1], values=[0.5])
        service = AsyncRetrievalService(
            RetrievalService(
                _StubChunkReadRepository(),
                LiteLLMChatSettings(),
                LiteLLMEmbeddingSettings(),
            )
        )

        # Act
        results = await service.search_documents("query", top_k=2, tenant_id="default")

        # Assert
        self.assertEqual([item.chunk_id for item in results], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
