import os
import unittest
from unittest.mock import patch

from agentic_shared.crosscut.auth.settings import AuthSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings


class TestSecuredStrSettings(unittest.TestCase):
    def test_litellm_master_key_is_masked_in_repr(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = LiteLLMChatSettings(_env_file=None, litellm_master_key="sk-super-secret")

        rendered = repr(settings)
        self.assertNotIn("sk-super-secret", rendered)
        self.assertIn("**********", rendered)
        self.assertEqual(settings.proxy_api_key, "sk-super-secret")

    def test_auth_api_key_is_masked_in_repr(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = AuthSettings(_env_file=None, api_key="dev-secret-key")

        rendered = repr(settings)
        self.assertNotIn("dev-secret-key", rendered)
        self.assertEqual(settings.api_key.get_secret_value(), "dev-secret-key")


if __name__ == "__main__":
    unittest.main()
