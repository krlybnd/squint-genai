import unittest
from unittest.mock import MagicMock, patch

from agentic_indexing.modules.pdf_indexing.pipeline import (
    _attach_short_headings,
    _join_pdf_pages,
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

    def test_join_pdf_pages_keeps_heading_split_across_pages(self) -> None:
        # Arrange
        page_one = MagicMock()
        page_one.metadata = {"page_label": 2}
        page_one.get_content.return_value = "Article."
        page_two = MagicMock()
        page_two.metadata = {"page_label": 3}
        page_two.get_content.return_value = (
            "I. Section. 1. All legislative Powers herein granted shall be vested in a Congress."
        )

        # Act
        joined = _join_pdf_pages(
            [page_one, page_two],
            doc_id="doc-1",
            source_file="us-constitution.pdf",
            tenant_id="acme",
        )

        # Assert
        self.assertEqual(len(joined), 1)
        text = joined[0].get_content()
        self.assertIn("Article.", text)
        self.assertIn("I. Section. 1.", text)
        self.assertEqual(joined[0].metadata["page"], 2)
        self.assertEqual(joined[0].metadata["source_file"], "us-constitution.pdf")

    def test_join_pdf_pages_skips_blank_pages(self) -> None:
        # Arrange
        blank = MagicMock()
        blank.metadata = {}
        blank.get_content.return_value = "  \n"
        filled = MagicMock()
        filled.metadata = {"page_label": 1}
        filled.get_content.return_value = "Congress"

        # Act
        joined = _join_pdf_pages(
            [blank, filled],
            doc_id="doc-1",
            source_file="us-constitution.pdf",
            tenant_id="acme",
        )

        # Assert
        self.assertEqual(joined[0].get_content(), "Congress")

    def test_attach_short_headings_keeps_article_label_with_section_body(self) -> None:
        # Arrange
        heading = MagicMock()
        heading.get_content.return_value = "Article. I."
        body = MagicMock()
        body.get_content.return_value = (
            "Section. 1. All legislative Powers herein granted shall be vested in a Congress "
            "of the United States, which shall consist of a Senate and House of Representatives."
        )

        # Act
        result = _attach_short_headings([heading, body])

        # Assert
        self.assertEqual(result, [body])
        combined = body.set_content.call_args[0][0]
        self.assertIn("Article. I.", combined)
        self.assertIn("All legislative Powers", combined)

    def test_attach_short_headings_leaves_long_chunks_alone(self) -> None:
        # Arrange
        first = MagicMock()
        first.get_content.return_value = "A" * 200
        second = MagicMock()
        second.get_content.return_value = "B" * 200

        # Act
        result = _attach_short_headings([first, second])

        # Assert
        self.assertEqual(result, [first, second])
        first.set_content.assert_not_called()
        second.set_content.assert_not_called()

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
        doc.get_content.return_value = "page text"
        mock_pdf_reader.return_value.load_data.return_value = [doc]
        empty_node = MagicMock()
        empty_node.get_content.return_value = ""
        mock_splitter_cls.return_value.get_nodes_from_documents.return_value = [empty_node]
        chunk_write = MagicMock()

        # Act
        count = index_pdf_bytes(
            b"pdf",
            doc_id="doc-1",
            source_file="file.pdf",
            tenant_id="acme",
            chunk_write=chunk_write,
            llm=MagicMock(litellm_base_url="http://llm", proxy_api_key="key"),
            embedding=MagicMock(embedding_model="embed"),
        )

        # Assert
        self.assertEqual(count, 0)
        chunk_write.index_nodes.assert_not_called()
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
        doc.get_content.return_value = "chunk"
        mock_pdf_reader.return_value.load_data.return_value = [doc]
        node = MagicMock()
        node.get_content.return_value = "chunk"
        node.metadata = {}
        mock_splitter_cls.return_value.get_nodes_from_documents.return_value = [node]
        chunk_write = MagicMock()
        chunk_write.index_nodes.return_value = 1

        # Act
        count = index_pdf_bytes(
            b"pdf",
            doc_id="doc-1",
            source_file="file.pdf",
            tenant_id="acme",
            chunk_write=chunk_write,
            llm=MagicMock(litellm_base_url="http://llm", proxy_api_key="key"),
            embedding=MagicMock(embedding_model="embed"),
        )

        # Assert
        self.assertEqual(count, 1)
        chunk_write.index_nodes.assert_called_once()
        mock_unlink.assert_called_once_with(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
