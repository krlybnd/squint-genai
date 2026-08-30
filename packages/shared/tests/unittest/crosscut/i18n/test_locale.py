import unittest

from agentic_shared.crosscut.i18n import resolve_locale, t, t_stored


class TestI18nLocale(unittest.TestCase):
    def test_resolve_locale_prefers_primary_tag(self) -> None:
        # Act / Assert
        self.assertEqual(resolve_locale("hu-HU,hu;q=0.9,en;q=0.8"), "hu")
        self.assertEqual(resolve_locale("de-DE,en;q=0.5"), "de")
        self.assertEqual(resolve_locale(None), "en")

    def test_translate_falls_back_to_english(self) -> None:
        # Act / Assert
        self.assertEqual(t("guard.ok", "hu"), "Biztonsági ellenőrzés OK.")
        self.assertEqual(t("missing.key", "hu"), "missing.key")

    def test_annotation_rejection_messages(self) -> None:
        # Act / Assert
        self.assertEqual(t("annotations.rejection.too_short", "en"), "Comment is too short.")
        self.assertEqual(t("annotations.rejection.too_short", "hu"), "A komment túl rövid.")
        self.assertIn("2000", t("annotations.rejection.too_long", "de", max=2000))

    def test_t_stored_translates_known_keys(self) -> None:
        # Act / Assert
        self.assertEqual(t_stored("jobs.cancelled_by_user", "hu"), "Felhasználó megszakította")
        self.assertEqual(t_stored("Some Celery traceback", "hu"), "Some Celery traceback")
        self.assertIsNone(t_stored(None, "en"))

    def test_moderation_system_prompt_keeps_json_braces(self) -> None:
        # Arrange
        reason = t("annotations.moderation.reason_instruction", "en", language="English")

        # Act
        prompt = t("annotations.moderation.system", "en", reason_instruction=reason)

        # Assert
        self.assertIn('"approved": boolean', prompt)
        self.assertIn("Reason in English when rejecting.", prompt)
        self.assertNotIn("{reason_instruction}", prompt)

    def test_resolve_locale_skips_unsupported_tags(self) -> None:
        # Act / Assert
        self.assertEqual(resolve_locale("fr-FR,en;q=0.8"), "en")
        self.assertEqual(resolve_locale("xx-YY,zz;q=0.9"), "en")

    def test_resolve_locale_ignores_empty_parts(self) -> None:
        # Act / Assert
        self.assertEqual(resolve_locale(" , ; ,hu-HU"), "hu")


if __name__ == "__main__":
    unittest.main()
