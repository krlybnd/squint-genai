import unittest
from unittest.mock import MagicMock

import httpx

from agentic_shared.integrations.litellm.analyzer.settings import (
    DEFAULT_ANALYZER_ENTITIES,
    AnalyzerSettings,
)
from agentic_shared.integrations.litellm.analyzer.sync_client import AnalyzerSyncClient


class TestAnalyzerSyncClient(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = AnalyzerSettings(analyzer_api_base="http://analyzer:3000/", _env_file=None)

    def test_analyze_maps_entities(self) -> None:
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status = MagicMock()
        response.json.return_value = [
            {"entity_type": "EMAIL_ADDRESS", "start": 10, "end": 20, "score": 0.99},
        ]
        http = MagicMock()
        http.post.return_value = response
        http.get.return_value = response
        client = AnalyzerSyncClient(self.settings)
        client._http = http

        entities = client.analyze("Contact a@b.com", language="en")

        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].entity_type, "EMAIL_ADDRESS")
        http.post.assert_called_once_with(
            "/analyze",
            json={
                "text": "Contact a@b.com",
                "language": "en",
                "entities": list(DEFAULT_ANALYZER_ENTITIES),
                "score_threshold": 0.3,
            },
        )
        client.close()

    def test_is_healthy_false_on_error(self) -> None:
        http = MagicMock()
        http.get.side_effect = httpx.ConnectError("down")
        client = AnalyzerSyncClient(self.settings)
        client._http = http
        self.assertFalse(client.is_healthy())
        client.close()


if __name__ == "__main__":
    unittest.main()
