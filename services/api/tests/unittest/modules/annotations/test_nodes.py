import unittest
from unittest.mock import AsyncMock, Mock, patch

from agentic_shared.crosscut.i18n import DEFAULT_LOCALE, t
from agentic_shared.integrations.litellm.guard.models import GuardResult

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

    def _deps(self, *, guard=None) -> CommentGraphDeps:
        if guard is None:
            guard = AsyncMock()
            guard.analyze_prompt.return_value = GuardResult(is_valid=True)
        return CommentGraphDeps(
            chat_client=AsyncMock(),
            embedding_client=AsyncMock(),
            comment_write=Mock(),
            guard=guard,
        )

    @patch(
        "agentic_api.modules.annotations.nodes.get_module_settings",
        return_value=AnnotationsModuleSettings(),
    )
    async def test_moderate_node_handles_json_parse_failure(
        self,
        _mock_settings: Mock,
    ) -> None:
        deps = self._deps()
        deps.chat_client.chat_completion.return_value = {
            "choices": [{"message": {"content": "not valid json"}}]
        }
        result = await moderate_node(self._state(), deps)

        self.assertFalse(result["approved"])
        self.assertEqual(
            result["rejection_reason"],
            t("annotations.rejection.moderation_failed", DEFAULT_LOCALE),
        )

    @patch(
        "agentic_api.modules.annotations.nodes.get_module_settings",
        return_value=AnnotationsModuleSettings(),
    )
    async def test_moderate_node_rejects_injection(self, _mock_settings: Mock) -> None:
        guard = AsyncMock()
        guard.analyze_prompt.return_value = GuardResult(is_valid=False)
        result = await moderate_node(self._state(), self._deps(guard=guard))

        self.assertFalse(result["approved"])
        self.assertEqual(
            result["rejection_reason"],
            t("annotations.rejection.injection", DEFAULT_LOCALE),
        )
        guard.analyze_prompt.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
