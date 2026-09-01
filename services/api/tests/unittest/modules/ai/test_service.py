import unittest

from agentic_shared.core.compliance import AiRiskTier, NoOpAiTransparency
from agentic_shared.core.compliance.settings import ComplianceSettings

from agentic_api.modules.ai.service import AiTransparencyService


class TestAiTransparencyService(unittest.TestCase):
    def test_system_card_maps_port_record(self) -> None:
        # Arrange
        port = NoOpAiTransparency(ComplianceSettings(ai_system_name="demo", ai_risk_tier="limited"))
        service = AiTransparencyService(port)

        # Act
        card = service.system_card()

        # Assert
        self.assertEqual(card.system_name, "demo")
        self.assertEqual(card.risk_tier, AiRiskTier.LIMITED.value)
        self.assertTrue(card.human_oversight)
        self.assertIn("question answering", card.purpose)


if __name__ == "__main__":
    unittest.main()
