import unittest
from unittest.mock import MagicMock, patch

from agentic_indexing.modules.pdf_indexing.pipeline import (
    _non_empty_nodes,
    index_pdf_bytes,
    materialize_nltk_cache,
)


class TestPdfIndexingPipeline(unittest.TestCase):
    def test_materialize_nltk_cache_is_idempotent(self) -> None:
        # Act
        first = materialize_nltk_cache()
        second = materialize_nltk_cache()

        # Assert
        self.assertGreaterEqual(first, 0)
        self.assertEqual(second, 0)

    def test_non_empty_nodes_filters_blank_content(self) -> None:
        # Arrange
        empty = MagicMock()
        empty.get_content.return_value = "   \n"
        populated = MagicMock()
        populated.get_content.return_value = "chunk text"

        # Act
        result = _non_empty_nodes([empty, populated])

        # Assert
        self.assertEqual(result, [populated])

    @patch("agentic_indexing.modules.pdf_indexing.pipeline.Path.unlink")
    @patch("agentic_indexing.modules.pdf_indexing.pipeline.SemanticSplitterNodeParser")
    @patch("agentic_indexing.modules.pdf_indexing.pipeline.PDFReader")
    @patch("agentic_indexing.modules.pdf_indexing.pipeline.OpenAIEmbedding")
    @patch("agentic_indexing.modules.pdf_indexing.pipeline.LISettings")
    @patch("agentic_indexing.modules.pdf_indexing.pipeline.materialize_nltk_cache")
    @patch("agentic_indexing.modules.pdf_indexing.pipeline.get_module_settings")
    def test_index_pdf_bytes_returns_zero_when_no_nodes(
        self,
        mock_get_module_settings: MagicMock,
        _mock_materialize_nltk_cache: MagicMock,
        _mock_li_settings: MagicMock,
        _mock_openai_embedding: MagicMock,
        mock_pdf_reader: MagicMock,
        mock_splitter_cls: MagicMock,
        mock_unlink: MagicMock,
    ) -> None:
        # Arrange
        mock_get_module_settings.return_value = MagicMock(
            semantic_buffer_size=1,
            semantic_breakpoint_percentile_threshold=95,
        )
        doc = MagicMock()
        doc.metadata = {"page_label": 1}
        mock_pdf_reader.return_value.load_data.return_value = [doc]
        empty_node = MagicMock()
        empty_node.get_content.return_value = ""
        mock_splitter_cls.return_value.get_nodes_from_documents.return_value = [empty_node]
        qdrant_write = MagicMock()

        # Act
        count = index_pdf_bytes(
            b"pdf",
            doc_id="doc-1",
            source_file="file.pdf",
            tenant_id="acme",
            qdrant_write=qdrant_write,
            llm=MagicMock(litellm_base_url="http://llm", proxy_api_key="key"),
            embedding=MagicMock(embedding_model="embed"),
        )

        # Assert
        self.assertEqual(count, 0)
        qdrant_write.index_nodes.assert_not_called()
        mock_unlink.assert_called_once_with(missing_ok=True)

    @patch("agentic_indexing.modules.pdf_indexing.pipeline.Path.unlink")
    @patch("agentic_indexing.modules.pdf_indexing.pipeline.SemanticSplitterNodeParser")
    @patch("agentic_indexing.modules.pdf_indexing.pipeline.PDFReader")
    @patch("agentic_indexing.modules.pdf_indexing.pipeline.OpenAIEmbedding")
    @patch("agentic_indexing.modules.pdf_indexing.pipeline.LISettings")
    @patch("agentic_indexing.modules.pdf_indexing.pipeline.materialize_nltk_cache")
    @patch("agentic_indexing.modules.pdf_indexing.pipeline.get_module_settings")
    def test_index_pdf_bytes_cleans_up_temp_file_on_success(
        self,
        mock_get_module_settings: MagicMock,
        _mock_materialize_nltk_cache: MagicMock,
        _mock_li_settings: MagicMock,
        _mock_openai_embedding: MagicMock,
        mock_pdf_reader: MagicMock,
        mock_splitter_cls: MagicMock,
        mock_unlink: MagicMock,
    ) -> None:
        # Arrange
        mock_get_module_settings.return_value = MagicMock(
            semantic_buffer_size=1,
            semantic_breakpoint_percentile_threshold=95,
        )
        doc = MagicMock()
        doc.metadata = {"page_label": 2}
        mock_pdf_reader.return_value.load_data.return_value = [doc]
        node = MagicMock()
        node.get_content.return_value = "chunk"
        node.metadata = {}
        mock_splitter_cls.return_value.get_nodes_from_documents.return_value = [node]
        qdrant_write = MagicMock()
        qdrant_write.index_nodes.return_value = 1

        # Act
        count = index_pdf_bytes(
            b"pdf",
            doc_id="doc-1",
            source_file="file.pdf",
            tenant_id="acme",
            qdrant_write=qdrant_write,
            llm=MagicMock(litellm_base_url="http://llm", proxy_api_key="key"),
            embedding=MagicMock(embedding_model="embed"),
        )

        # Assert
        self.assertEqual(count, 1)
        qdrant_write.index_nodes.assert_called_once()
        mock_unlink.assert_called_once_with(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
