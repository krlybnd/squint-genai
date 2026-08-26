import unittest

from agentic_shared.core.security.guard.pii import redact_pii


class TestGuardPii(unittest.TestCase):
    def test_redact_email(self) -> None:
        # Act
        result = redact_pii("Írj a user@example.com címre")

        # Assert
        self.assertIn("[EMAIL_REDACTED]", result.text)
        self.assertGreaterEqual(result.count, 1)

    def test_redact_phone_hu(self) -> None:
        # Act / Assert
        result = redact_pii("Hívj: +36 30 123 4567")
        self.assertIn("[PHONE_REDACTED]", result.text)

    def test_redact_sensitive_field(self) -> None:
        # Act / Assert
        result = redact_pii("név: Nagy János")
        self.assertIn("[PII_REDACTED]", result.text)

    def test_no_redaction_for_normal_query(self) -> None:
        # Act
        result = redact_pii("Mi van a cucu.pdf dokumentumban?")

        # Assert
        self.assertEqual(result.text, "Mi van a cucu.pdf dokumentumban?")
        self.assertEqual(result.count, 0)

    def test_redact_iban_and_records_details(self) -> None:
        # Act
        result = redact_pii("Transfer to HU42117730161111101800000000")

        # Assert
        self.assertIn("[IBAN_REDACTED]", result.text)
        self.assertGreaterEqual(result.count, 1)
        kinds = {detail.kind for detail in result.details}
        self.assertIn("iban", kinds)

    def test_redact_ip_address(self) -> None:
        # Act / Assert
        result = redact_pii("Server at 192.168.1.42 responded")
        self.assertIn("[IP_REDACTED]", result.text)

    def test_redact_passport_number(self) -> None:
        # Act / Assert
        result = redact_pii("Passport P1234567")
        self.assertIn("[PASSPORT_REDACTED]", result.text)

    def test_empty_string_returns_zero_count(self) -> None:
        # Act
        result = redact_pii("")

        # Assert
        self.assertEqual(result.text, "")
        self.assertEqual(result.count, 0)
        self.assertEqual(result.details, [])


if __name__ == "__main__":
    unittest.main()
