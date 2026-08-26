import unittest

from agentic_shared.domains.chat.roles import LlmMessageRole
from agentic_shared.integrations.llm.messages import llm_completion_messages, llm_system_user


class TestLlmMessages(unittest.TestCase):
    def test_llm_completion_messages_serializes_roles(self) -> None:
        # Act
        messages = llm_completion_messages(
            (LlmMessageRole.SYSTEM, "You are helpful."),
            (LlmMessageRole.USER, "Hi"),
        )

        # Assert
        self.assertEqual(
            messages,
            [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hi"},
            ],
        )

    def test_llm_completion_messages_coerces_none_content_to_empty_string(self) -> None:
        # Act / Assert
        messages = llm_completion_messages((LlmMessageRole.ASSISTANT, ""))
        self.assertEqual(messages[0]["content"], "")

    def test_llm_system_user_builds_system_and_user_pair(self) -> None:
        # Act
        messages = llm_system_user("Rules", "Question?")

        # Assert
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], "Rules")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "Question?")


if __name__ == "__main__":
    unittest.main()
