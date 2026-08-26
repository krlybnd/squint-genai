import unittest
from datetime import UTC, datetime
from uuid import uuid4

from agentic_shared.domains.chat.roles import ChatMessageRole
from agentic_shared.domains.persistence.entities import ChatMessage
from agentic_shared.domains.retrieval.models import ChunkCitation

from agentic_chat.core.state import GraphMessage
from agentic_chat.modules.chat.schemas import ChatMessageOut, CitationOut, to_graph_messages


class TestCitations(unittest.TestCase):
    def test_citation_out_from_citation(self) -> None:
        # Arrange
        citation = ChunkCitation(
            chunk_id="c1",
            doc_id="d1",
            source_file="paper.pdf",
            page=2,
            excerpt="hello",
        )

        # Act
        out = CitationOut.from_citation(citation)

        # Assert
        self.assertEqual(out.chunk_id, "c1")
        self.assertEqual(out.source_file, "paper.pdf")

    def test_citation_out_list_from_stored_skips_invalid(self) -> None:
        # Arrange
        stored = [
            {"chunk_id": "c1", "excerpt": "ok"},
            "bad",
            {"chunk_id": 123},
        ]

        # Act
        parsed = CitationOut.list_from_stored(stored)

        # Assert
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].chunk_id, "c1")

    def test_chat_message_out_from_entity(self) -> None:
        # Arrange
        entity = ChatMessage(
            id=uuid4(),
            session_id=uuid4(),
            role=ChatMessageRole.USER,
            content="hello",
            citations_json='[{"chunk_id": "c1", "excerpt": "x"}]',
            created_at=datetime.now(UTC),
        )

        # Act
        out = ChatMessageOut.from_entity(entity)
        graph = to_graph_messages([out])

        # Assert
        self.assertIs(out.role, ChatMessageRole.USER)
        self.assertEqual(len(out.citations), 1)
        self.assertEqual(graph, [GraphMessage(role=ChatMessageRole.USER, content="hello")])


if __name__ == "__main__":
    unittest.main()
