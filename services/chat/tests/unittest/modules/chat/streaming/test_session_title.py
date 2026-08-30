import unittest

from agentic_shared.crosscut.i18n import LOCALE_LANGUAGE, t

from agentic_chat.modules.chat.streaming.session_title import (
    SessionTitleGenerator,
    default_session_title,
)


class TestSessionTitle(unittest.TestCase):
    def test_default_session_title_localized(self) -> None:
        # Act / Assert
        self.assertEqual(default_session_title("hu"), "Új beszélgetés")
        self.assertEqual(default_session_title("en"), "New chat")

    def test_is_default_title_accepts_all_locale_defaults(self) -> None:
        # Act / Assert
        self.assertTrue(SessionTitleGenerator.is_default_title("New chat"))
        self.assertTrue(SessionTitleGenerator.is_default_title("Új beszélgetés"))
        self.assertTrue(SessionTitleGenerator.is_default_title("Neuer Chat"))
        self.assertFalse(SessionTitleGenerator.is_default_title("PDF összefoglaló"))

    def test_title_system_prompt_uses_locale(self) -> None:
        # Act
        hu = t("session.title_system_prompt", "hu", language=LOCALE_LANGUAGE["hu"])

        # Assert
        self.assertTrue("3–8" in hu or "3-8" in hu)
        self.assertIn(LOCALE_LANGUAGE["hu"], hu)


if __name__ == "__main__":
    unittest.main()
