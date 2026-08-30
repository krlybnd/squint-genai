import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity
from agentic_shared.integrations.litellm.anonymizer.client import AnonymizerClient
from agentic_shared.integrations.litellm.anonymizer.settings import AnonymizerSettings


class TestAnonymizerClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = AnonymizerSettings(
            anonymizer_api_base="http://anonymizer:3000/",
            _env_file=None,
        )

    @patch("agentic_shared.integrations.litellm.anonymizer.client.httpx.AsyncClient")
    async def test_anonymize_returns_text(self, http_cls: MagicMock) -> None:
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {"text": "Contact <EMAIL_ADDRESS>"}
        http = MagicMock()
        http.post = AsyncMock(return_value=response)
        http.aclose = AsyncMock()
        http_cls.return_value = http

        client = AnonymizerClient(self.settings)
        entity = AnalyzerEntity(entity_type="EMAIL_ADDRESS", start=8, end=16, score=1.0)
        result = await client.anonymize("Contact a@b.com", [entity])

        self.assertEqual(result.text, "Contact <EMAIL_ADDRESS>")
        await client.aclose()


class TestAnonymizerSettings(unittest.TestCase):
    def test_defaults(self) -> None:
        self.assertEqual(AnonymizerSettings(_env_file=None).title, "anonymizer")


if __name__ == "__main__":
    unittest.main()
