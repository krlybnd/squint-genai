import os
import unittest
from unittest.mock import patch

from agentic_shared.integrations.litellm.core.settings import LiteLLMSettings
from agentic_shared.integrations.litellm.embedding.settings import (
    EmbeddingSettings,
    LiteLLMEmbeddingSettings,
)
from agentic_shared.integrations.litellm.llm.settings import ChatSettings, LiteLLMChatSettings


class TestIntegrationSettingsInheritance(unittest.TestCase):
    def test_base_embedding_settings_defaults_without_env(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = EmbeddingSettings(_env_file=None)

        self.assertEqual(settings.title, "embedding")
        self.assertEqual(settings.embedding_model, "embed")

    def test_litellm_embedding_overrides_title(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = LiteLLMEmbeddingSettings(_env_file=None)

        self.assertEqual(settings.title, "litellm-embedding")
        self.assertEqual(settings.embedding_model, "embed")
        self.assertIsInstance(settings, EmbeddingSettings)

    def test_base_chat_settings_defaults_without_env(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = ChatSettings(_env_file=None)

        self.assertEqual(settings.title, "chat")

    def test_litellm_chat_role_alias_defaults(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            llm = LiteLLMChatSettings(_env_file=None)

        self.assertEqual(llm.title, "litellm-chat")
        self.assertEqual(llm.litellm_model, "generate")
        self.assertEqual(llm.litellm_router_model, "router")
        self.assertEqual(llm.litellm_judge_model, "judge")
        self.assertNotEqual(llm.litellm_model, llm.litellm_judge_model)
        self.assertIsInstance(llm, LiteLLMSettings)


if __name__ == "__main__":
    unittest.main()
