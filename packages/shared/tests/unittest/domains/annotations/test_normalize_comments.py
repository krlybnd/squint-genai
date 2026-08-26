import unittest

from agentic_shared.domains.annotations.models import ChunkComment
from agentic_shared.infrastructure.vector.comments import normalize_comments


class TestNormalizeComments(unittest.TestCase):
    def test_normalize_comments_validates_pydantic(self) -> None:
        # Arrange
        payload = {
            "comments": [
                {
                    "comment_id": "c1",
                    "selected_text": "excerpt",
                    "comment_text": "note",
                    "created_at": "2026-01-01T00:00:00Z",
                },
                {"comment_id": "", "comment_text": "bad"},
                "not-a-dict",
            ]
        }

        # Act
        comments = normalize_comments(payload)

        # Assert
        self.assertEqual(len(comments), 1)
        self.assertEqual(
            comments[0],
            ChunkComment(
                comment_id="c1",
                selected_text="excerpt",
                comment_text="note",
                user_id=None,
                created_at="2026-01-01T00:00:00Z",
            ),
        )


if __name__ == "__main__":
    unittest.main()
