import unittest

from agentic_shared.domains.chat.enums import ChatMessageRole


class TestChatMessageRole(unittest.TestCase):
    def test_chat_message_role_from_stored(self) -> None:
        # Arrange / Act / Assert
        self.assertIs(ChatMessageRole.from_stored("assistant"), ChatMessageRole.ASSISTANT)
        self.assertIs(ChatMessageRole.from_stored("user"), ChatMessageRole.USER)
        self.assertIs(ChatMessageRole.from_stored("system"), ChatMessageRole.USER)


if __name__ == "__main__":
    unittest.main()
