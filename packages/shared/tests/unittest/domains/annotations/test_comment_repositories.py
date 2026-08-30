import unittest
from unittest.mock import MagicMock

from agentic_shared.domains.annotations.models import ChunkComment
from agentic_shared.domains.annotations.repositories.qdrant_.comments import (
    QdrantCommentReadRepository,
    QdrantCommentWriteRepository,
)


def _point(payload: dict) -> MagicMock:
    return MagicMock(payload=payload)


class TestQdrantCommentRepositories(unittest.TestCase):
    def test_list_for_chunk_returns_comments(self) -> None:
        # Arrange
        client = MagicMock()
        client.collection_name = "test"
        client._sdk.retrieve.return_value = [
            _point(
                {
                    "tenant_id": "tenant-a",
                    "comments": [
                        {
                            "comment_id": "c1",
                            "comment_text": "note",
                            "created_at": "2026-01-01T00:00:00Z",
                        }
                    ],
                }
            )
        ]
        repo = QdrantCommentReadRepository(client)

        # Act
        comments = repo.list_for_chunk("chunk-1", tenant_id="tenant-a")

        # Assert
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].comment_id, "c1")

    def test_append_to_chunk_updates_payload(self) -> None:
        # Arrange
        client = MagicMock()
        client.collection_name = "test"
        client._sdk.retrieve.return_value = [_point({"tenant_id": "tenant-a", "comments": []})]
        repo = QdrantCommentWriteRepository(client)
        comment = ChunkComment(
            comment_id="c2",
            comment_text="new note",
            created_at="2026-01-02T00:00:00Z",
        )

        # Act
        repo.append_to_chunk("chunk-1", comment, tenant_id="tenant-a")

        # Assert
        client._sdk.set_payload.assert_called_once()
        call_kwargs = client._sdk.set_payload.call_args.kwargs
        self.assertEqual(call_kwargs["points"], ["chunk-1"])
        self.assertEqual(len(call_kwargs["payload"]["comments"]), 1)
        self.assertEqual(call_kwargs["payload"]["comments"][0]["comment_id"], "c2")


if __name__ == "__main__":
    unittest.main()
