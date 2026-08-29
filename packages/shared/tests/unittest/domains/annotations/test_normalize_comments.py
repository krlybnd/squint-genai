import unittest

from agentic_shared.domains.annotations.models import ChunkComment
from agentic_shared.domains.annotations.normalize import normalize_comments


class TestNormalizeComments(unittest.TestCase):
    def test_normalize_comments_validates_pydantic(self) -> None:
        # Arrange
        raw = [
            {
                "comment_id": "c1",
                "selected_text": "excerpt",
                "comment_text": "note",
                "created_at": "2026-01-01T00:00:00Z",
            },
            {"comment_id": "", "comment_text": "bad"},
            "not-a-dict",
        ]

        # Act
        comments = normalize_comments(raw)

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

    def test_normalize_comments_empty_and_invalid(self) -> None:
        # Act / Assert
        self.assertEqual(normalize_comments(None), [])
        self.assertEqual(normalize_comments({}), [])
        self.assertEqual(normalize_comments("not-a-list"), [])

    def test_normalize_comments_skips_invalid_entries(self) -> None:
        # Arrange
        raw = [
            {
                "comment_id": "c1",
                "comment_text": "valid",
                "created_at": "2026-01-01T00:00:00Z",
            },
            {"comment_id": "", "comment_text": "bad"},
            "not-a-dict",
        ]

        # Act
        comments = normalize_comments(raw)

        # Assert
        self.assertEqual(len(comments), 1)
        self.assertEqual(
            comments[0],
            ChunkComment(
                comment_id="c1",
                selected_text="",
                comment_text="valid",
                user_id=None,
                created_at="2026-01-01T00:00:00Z",
            ),
        )


if __name__ == "__main__":
    unittest.main()
