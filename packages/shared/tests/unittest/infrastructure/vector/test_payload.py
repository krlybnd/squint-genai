import json
import unittest

from agentic_shared.infrastructure.vector.payload import payload_page, payload_text
from agentic_shared.infrastructure.vector.types import VectorPayload


class TestVectorPayload(unittest.TestCase):
    def test_payload_text_prefers_direct_text_field(self) -> None:
        # Arrange
        payload = VectorPayload.model_validate(
            {"text": "  hello world  ", "_node_content": '{"text":"ignored"}'}
        )

        # Act / Assert
        self.assertEqual(payload_text(payload), "hello world")

    def test_payload_text_parses_node_content_json(self) -> None:
        # Arrange
        node = json.dumps({"text": "from node", "metadata": {"page": 1}})
        payload = VectorPayload.model_validate({"_node_content": node})

        # Act / Assert
        self.assertEqual(payload_text(payload), "from node")

    def test_payload_text_returns_raw_when_json_invalid(self) -> None:
        # Arrange
        payload = VectorPayload.model_validate({"_node_content": "  plain fallback  "})

        # Act / Assert
        self.assertEqual(payload_text(payload), "plain fallback")

    def test_payload_text_empty_payload(self) -> None:
        # Act / Assert
        self.assertEqual(payload_text(VectorPayload.model_validate({})), "")
        self.assertEqual(
            payload_text(VectorPayload.model_validate({"_node_content": ""})),
            "",
        )

    def test_payload_page_prefers_page_over_page_label(self) -> None:
        # Act / Assert
        self.assertEqual(
            payload_page(VectorPayload.model_validate({"page": 3, "page_label": "III"})),
            3,
        )

    def test_payload_page_falls_back_to_page_label(self) -> None:
        # Act / Assert
        self.assertEqual(
            payload_page(VectorPayload.model_validate({"page_label": "12"})),
            "12",
        )

    def test_payload_page_none_when_missing(self) -> None:
        # Act / Assert
        self.assertIsNone(payload_page(VectorPayload.model_validate({})))


if __name__ == "__main__":
    unittest.main()
