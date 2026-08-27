import unittest

from agentic_shared.domains.retrieval.tool_catalog import (
    ALL_TOOLS,
    SEARCH_DOCUMENTS,
    format_retrieval_tools_prompt_for_query_rewrite,
    format_tool_doc,
)


class TestRetrievalToolCatalog(unittest.TestCase):
    def test_format_tool_doc_includes_sections(self) -> None:
        # Act
        doc = format_tool_doc(SEARCH_DOCUMENTS)

        # Assert
        self.assertIn("### search_documents", doc)
        self.assertIn("Parameters:", doc)
        self.assertIn("Query / usage guidelines:", doc)
        self.assertIn("Returns:", doc)
        self.assertIn("Hybrid search", doc)
        self.assertIn("Do not translate the query into another language.", doc)

    def test_format_retrieval_tools_prompt_lists_all_tools(self) -> None:
        # Act
        prompt = format_retrieval_tools_prompt_for_query_rewrite()

        # Assert
        self.assertIn("search_documents.query", prompt)
        for tool in ALL_TOOLS:
            self.assertIn(f"### {tool.name}", prompt)

    def test_format_retrieval_tools_prompt_separates_blocks(self) -> None:
        # Act / Assert
        prompt = format_retrieval_tools_prompt_for_query_rewrite()
        self.assertIn("\n\n### get_source_citation\n", prompt)


if __name__ == "__main__":
    unittest.main()
