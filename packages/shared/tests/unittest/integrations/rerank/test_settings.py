import os
import unittest
from unittest.mock import patch

from agentic_shared.integrations.rerank.settings import RerankSettings


class TestRerankSettings(unittest.TestCase):
    def test_rerank_auto_disabled_without_cohere_key(self) -> None:
        # Act / Assert
        with patch.dict(os.environ, {"RERANK_ENABLED": "true", "COHERE_API_KEY": ""}, clear=False):
            settings = RerankSettings()
            self.assertFalse(settings.rerank_enabled)

    def test_rerank_enabled_with_cohere_key(self) -> None:
        # Act / Assert
        with patch.dict(
            os.environ, {"RERANK_ENABLED": "true", "COHERE_API_KEY": "test-key"}, clear=False
        ):
            settings = RerankSettings()
            self.assertTrue(settings.rerank_enabled)


if __name__ == "__main__":
    unittest.main()
