import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from qdrant_client.http.models import SparseVector

from agentic_shared.domains.retrieval.models import RetrievedChunk
from agentic_shared.domains.retrieval.service import AsyncRetrievalService, RetrievalService
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings
from agentic_shared.integrations.rerank.settings import RerankSettings


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
    def test_search_documents_reranks_hybrid_candidates(
        self,
        mock_dense,
        mock_sparse,
    ) -> None:
        # Arrange
        mock_dense.return_value = [0.1, 0.2]
        mock_sparse.return_value = SparseVector(indices=[1], values=[0.5])
        rerank_client = MagicMock()
        rerank_client.rerank.return_value = [2, 0]
        rerank_settings = RerankSettings.model_construct(
            title="rerank",
            rerank_enabled=True,
            rerank_model="rerank-multilingual-v3.0",
        )
        service = RetrievalService(
            _StubChunkReadRepository(),
            LLMSettings(),
            EmbeddingSettings(),
            rerank_settings,
            rerank_client=rerank_client,
        )

        # Act
        results = service.search_documents("query", top_k=2, tenant_id="default")

        # Assert
        rerank_client.rerank.assert_called_once()
        self.assertEqual([item.chunk_id for item in results], ["c", "a"])

    @patch("agentic_shared.domains.retrieval.service.embed_sparse_text")
    @patch("agentic_shared.domains.retrieval.service.embed_dense_text")
    def test_search_documents_skips_rerank_when_disabled(
        self,
        mock_dense,
        mock_sparse,
    ) -> None:
        # Arrange
        mock_dense.return_value = [0.1, 0.2]
        mock_sparse.return_value = SparseVector(indices=[1], values=[0.5])
        service = RetrievalService(
            _StubChunkReadRepository(),
            LLMSettings(),
            EmbeddingSettings(),
            RerankSettings(rerank_enabled=False),
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
            LLMSettings(),
            EmbeddingSettings(),
            RerankSettings(rerank_enabled=True, cohere_api_key="test-key"),
        )

        # Act
        result = service.search_documents_with_meta("   ", tenant_id="default")

        # Assert
        self.assertEqual(result.chunks, [])
        mock_dense.assert_not_called()
        mock_sparse.assert_not_called()

    @patch("agentic_shared.domains.retrieval.service.embed_sparse_text")
    @patch("agentic_shared.domains.retrieval.service.embed_dense_text")
    def test_search_documents_falls_back_when_rerank_fails(
        self,
        mock_dense,
        mock_sparse,
    ) -> None:
        # Arrange
        mock_dense.return_value = [0.1]
        mock_sparse.return_value = SparseVector(indices=[1], values=[0.5])
        rerank_client = MagicMock()
        rerank_client.rerank.side_effect = RuntimeError("rerank down")
        rerank_settings = RerankSettings.model_construct(
            title="rerank",
            rerank_enabled=True,
            rerank_model="rerank-multilingual-v3.0",
            cohere_api_key="test-key",
        )
        service = RetrievalService(
            _StubChunkReadRepository(),
            LLMSettings(),
            EmbeddingSettings(),
            rerank_settings,
            rerank_client=rerank_client,
        )

        # Act
        result = service.search_documents_with_meta("query", top_k=2, tenant_id="default")

        # Assert
        self.assertEqual([item.chunk_id for item in result.chunks], ["a", "b"])
        self.assertIn("rerank down", result.meta.rerank_error or "")

    @patch("agentic_shared.domains.retrieval.service.embed_sparse_text")
    @patch("agentic_shared.domains.retrieval.service.embed_dense_text")
    def test_search_documents_skips_rerank_for_single_candidate(
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

        rerank_client = MagicMock()
        rerank_settings = RerankSettings.model_construct(
            title="rerank",
            rerank_enabled=True,
            rerank_model="rerank-multilingual-v3.0",
            cohere_api_key="test-key",
        )
        service = RetrievalService(
            _SingleHitReader(),
            LLMSettings(),
            EmbeddingSettings(),
            rerank_settings,
            rerank_client=rerank_client,
        )

        # Act
        result = service.search_documents_with_meta("query", top_k=1, tenant_id="default")

        # Assert
        rerank_client.rerank.assert_not_called()
        self.assertEqual([item.chunk_id for item in result.chunks], ["only"])


class TestRetrievalPipelineAsync(unittest.IsolatedAsyncioTestCase):
    @patch("agentic_shared.domains.retrieval.service.embed_sparse_text")
    @patch("agentic_shared.domains.retrieval.service.embed_dense_text")
    async def test_search_documents_async_reranks_hybrid_candidates(
        self,
        mock_dense,
        mock_sparse,
    ) -> None:
        # Arrange
        mock_dense.return_value = [0.1, 0.2]
        mock_sparse.return_value = SparseVector(indices=[1], values=[0.5])
        rerank_client = MagicMock()
        rerank_client.rerank_async = AsyncMock(return_value=[2, 0])
        rerank_settings = RerankSettings.model_construct(
            title="rerank",
            rerank_enabled=True,
            rerank_model="rerank-multilingual-v3.0",
        )
        service = AsyncRetrievalService(
            RetrievalService(
                _StubChunkReadRepository(),
                LLMSettings(),
                EmbeddingSettings(),
                rerank_settings,
                rerank_client=rerank_client,
            )
        )

        # Act
        results = await service.search_documents("query", top_k=2, tenant_id="default")

        # Assert
        rerank_client.rerank_async.assert_awaited_once()
        self.assertEqual([item.chunk_id for item in results], ["c", "a"])


if __name__ == "__main__":
    unittest.main()
