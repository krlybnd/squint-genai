import unittest

from agentic_shared.integrations.litellm.llm.content import extract_chat_completion_content
from agentic_shared.integrations.litellm.llm.models import ChatCompletionResult


class TestLlmContent(unittest.TestCase):
    def test_extract_from_chat_completion_result(self) -> None:
        # Arrange
        result = ChatCompletionResult.model_validate(
            {"choices": [{"message": {"role": "assistant", "content": "Hello"}}]}
        )

        # Act / Assert
        self.assertEqual(extract_chat_completion_content(result), "Hello")

    def test_extract_from_api_response_dict(self) -> None:
        # Arrange
        data = {"choices": [{"message": {"role": "assistant", "content": "From dict"}}]}

        # Act / Assert
        self.assertEqual(extract_chat_completion_content(data), "From dict")

    def test_extract_returns_empty_for_unknown_type(self) -> None:
        # Act / Assert
        self.assertEqual(extract_chat_completion_content("not-a-result"), "")
        self.assertEqual(extract_chat_completion_content(None), "")

    def test_extract_empty_choices(self) -> None:
        # Act / Assert
        self.assertEqual(extract_chat_completion_content({"choices": []}), "")


if __name__ == "__main__":
    unittest.main()
