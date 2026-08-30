import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from agentic_shared.integrations.litellm.analyzer.client import AnalyzerClient
from agentic_shared.integrations.litellm.analyzer.errors import AnalyzerError
from agentic_shared.integrations.litellm.analyzer.settings import AnalyzerSettings


class TestAnalyzerClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = AnalyzerSettings(
            analyzer_api_base="http://analyzer:3000/",
            _env_file=None,
        )

    @patch("agentic_shared.integrations.litellm.analyzer.client.httpx.AsyncClient")
    async def test_analyze_maps_entities(self, http_cls: MagicMock) -> None:
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status = MagicMock()
        response.json.return_value = [
            {"entity_type": "EMAIL_ADDRESS", "start": 10, "end": 20, "score": 0.99},
        ]
        http = MagicMock()
        http.post = AsyncMock(return_value=response)
        http.aclose = AsyncMock()
        http_cls.return_value = http

        client = AnalyzerClient(self.settings)
        entities = await client.analyze("Contact a@b.com", language="en")

        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].entity_type, "EMAIL_ADDRESS")
        await client.aclose()

    @patch("agentic_shared.integrations.litellm.analyzer.client.httpx.AsyncClient")
    async def test_analyze_wraps_http_error(self, http_cls: MagicMock) -> None:
        http = MagicMock()
        http.post = AsyncMock(side_effect=httpx.ConnectError("down"))
        http.aclose = AsyncMock()
        http_cls.return_value = http

        client = AnalyzerClient(self.settings)
        with self.assertRaises(AnalyzerError):
            await client.analyze("x")
        await client.aclose()


class TestAnalyzerSettings(unittest.TestCase):
    def test_defaults(self) -> None:
        self.assertEqual(AnalyzerSettings(_env_file=None).title, "analyzer")


if __name__ == "__main__":
    unittest.main()
