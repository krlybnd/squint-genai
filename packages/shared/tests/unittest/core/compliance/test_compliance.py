import unittest

from agentic_shared.core.compliance import AiRiskTier, ComplianceSettings, NoOpAiTransparency


class TestCompliance(unittest.TestCase):
    def test_ai_transparency_custom_tier(self) -> None:
        # Arrange
        settings = ComplianceSettings(ai_risk_tier="minimal")

        # Act
        record = NoOpAiTransparency(settings).system_record()

        # Assert
        self.assertEqual(record.risk_tier, AiRiskTier.MINIMAL)


if __name__ == "__main__":
    unittest.main()
