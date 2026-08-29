import unittest
from unittest.mock import AsyncMock, Mock, patch

from agentic_shared.core.i18n import DEFAULT_LOCALE, t

from agentic_api.modules.annotations.deps import CommentGraphDeps
from agentic_api.modules.annotations.nodes import moderate_node
from agentic_api.modules.annotations.settings import AnnotationsModuleSettings


class TestModerationNodes(unittest.IsolatedAsyncioTestCase):
    def _state(self) -> dict[str, str]:
        return {
            "chunk_id": "chunk-1",
            "selected_text": "Selected excerpt",
            "comment_text": "This is a valid comment",
            "locale": DEFAULT_LOCALE,
        }

    def _deps(self) -> CommentGraphDeps:
        return CommentGraphDeps(
            chat_client=AsyncMock(),
            embedding_client=AsyncMock(),
            comment_write=Mock(),
        )

    @patch("agentic_api.modules.annotations.nodes.looks_like_prompt_injection", return_value=False)
    @patch("agentic_api.modules.annotations.nodes.get_module_settings")
    async def test_moderate_node_handles_json_parse_failure(
        self,
        mock_get_module_settings: Mock,
        _mock_injection: Mock,
    ) -> None:
        # Arrange
        mock_get_module_settings.return_value = AnnotationsModuleSettings()
        deps = self._deps()
        deps.chat_client.chat_completion.return_value = {
            "choices": [{"message": {"content": "not valid json"}}]
        }

        # Act
        result = await moderate_node(self._state(), deps)

        # Assert
        self.assertFalse(result["approved"])
        self.assertEqual(
            result["rejection_reason"],
            t("annotations.rejection.moderation_failed", DEFAULT_LOCALE),
        )


if __name__ == "__main__":
    unittest.main()
