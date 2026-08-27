import os
import unittest
from unittest.mock import patch

from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings
from agentic_shared.integrations.rerank.settings import RerankSettings


class TestLlmRoleAliasDefaults(unittest.TestCase):
    def test_defaults_are_proxy_role_aliases(self) -> None:
        # Arrange / Act
        with patch.dict(os.environ, {}, clear=True):
            llm = LLMSettings(_env_file=None)
            embedding = EmbeddingSettings(_env_file=None)
            rerank = RerankSettings(_env_file=None)

        # Assert
        self.assertEqual(llm.litellm_model, "generate")
        self.assertEqual(llm.litellm_router_model, "router")
        self.assertEqual(llm.litellm_judge_model, "judge")
        self.assertEqual(embedding.embedding_model, "embed")
        self.assertEqual(rerank.rerank_model, "rerank")
        self.assertNotEqual(llm.litellm_model, llm.litellm_judge_model)


if __name__ == "__main__":
    unittest.main()
