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

    def test_default_entities_exclude_noisy_recognizers(self) -> None:
        entities = AnalyzerSettings(_env_file=None).analyzer_entities
        self.assertIn("PERSON", entities)
        self.assertIn("IBAN_CODE", entities)
        self.assertNotIn("DATE_TIME", entities)
        self.assertNotIn("US_BANK_NUMBER", entities)
        self.assertNotIn("US_DRIVER_LICENSE", entities)

    def test_payload_carries_detection_limits(self) -> None:
        settings = AnalyzerSettings(
            analyzer_entities=["PERSON"],
            analyzer_score_threshold=0.5,
            analyzer_allow_list=["Gamma"],
            _env_file=None,
        )
        self.assertEqual(
            settings.analyze_payload("hi", language="en"),
            {
                "text": "hi",
                "language": "en",
                "entities": ["PERSON"],
                "score_threshold": 0.5,
                "allow_list": ["Gamma"],
                "allow_list_match": "regex",
            },
        )

    def test_payload_omits_unset_limits(self) -> None:
        settings = AnalyzerSettings(
            analyzer_entities=[],
            analyzer_score_threshold=0.0,
            _env_file=None,
        )
        self.assertEqual(
            settings.analyze_payload("hi", language="en"),
            {"text": "hi", "language": "en"},
        )

    def test_term_lists_accept_comma_separated_env(self) -> None:
        settings = AnalyzerSettings(
            analyzer_entities="PERSON, IBAN_CODE",
            analyzer_allow_list="Gamma, KAH",
            _env_file=None,
        )
        self.assertEqual(settings.analyzer_entities, ["PERSON", "IBAN_CODE"])
        self.assertEqual(settings.analyzer_allow_list, ["Gamma", "KAH"])

    def test_term_lists_accept_json_env(self) -> None:
        settings = AnalyzerSettings(analyzer_entities='["PERSON"]', _env_file=None)
        self.assertEqual(settings.analyzer_entities, ["PERSON"])


if __name__ == "__main__":
    unittest.main()
