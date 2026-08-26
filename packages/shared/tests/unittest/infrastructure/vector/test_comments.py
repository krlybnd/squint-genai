import unittest

from agentic_shared.domains.annotations.models import ChunkComment
from agentic_shared.infrastructure.vector.comments import (
    contains_obscene_language,
    normalize_comments,
)


class TestVectorComments(unittest.TestCase):
    def test_contains_obscene_language_detects_terms(self) -> None:
        # Act / Assert
        self.assertTrue(contains_obscene_language("This is fucking unacceptable"))
        self.assertTrue(contains_obscene_language("Ez kurva jó"))
        self.assertFalse(contains_obscene_language("Normal technical comment about APIs"))

    def test_contains_obscene_language_substring_in_token(self) -> None:
        # Act / Assert
        self.assertTrue(contains_obscene_language("whatthefuck"))

    def test_normalize_comments_empty_and_invalid(self) -> None:
        # Act / Assert
        self.assertEqual(normalize_comments(None), [])
        self.assertEqual(normalize_comments({}), [])
        self.assertEqual(normalize_comments({"comments": "not-a-list"}), [])

    def test_normalize_comments_skips_invalid_entries(self) -> None:
        # Arrange
        payload = {
            "comments": [
                {
                    "comment_id": "c1",
                    "comment_text": "valid",
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
                selected_text="",
                comment_text="valid",
                user_id=None,
                created_at="2026-01-01T00:00:00Z",
            ),
        )


if __name__ == "__main__":
    unittest.main()
