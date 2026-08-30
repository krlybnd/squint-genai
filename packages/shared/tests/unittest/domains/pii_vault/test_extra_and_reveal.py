import unittest

from agentic_shared.domains.pii_vault.extra_recognizers import supplement_analyzer_entities
from agentic_shared.domains.pii_vault.reveal_service import StreamingVaultReveal, VaultRevealService
from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity


class TestExtraRecognizers(unittest.TestCase):
    def test_adds_hu_tax_number(self) -> None:
        text = "Tax id 12345678-1-23 applies."
        entities = supplement_analyzer_entities(text, [])
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].entity_type, "HU_TAX_NUMBER")

    def test_skips_overlapping_span(self) -> None:
        text = "12345678-1-23"
        existing = [AnalyzerEntity(entity_type="ID", start=0, end=len(text), score=0.5)]
        entities = supplement_analyzer_entities(text, existing)
        self.assertEqual(len(entities), 1)


class _FakeVault:
    async def resolve_tokens(self, tokens):
        from agentic_shared.core.settings.secrets import SecuredStr

        return {"<PERSON_AABBCCDD>": SecuredStr("Jane VaultTest")}


class TestVaultRevealService(unittest.IsolatedAsyncioTestCase):
    async def test_reveal_text_replaces_tokens(self) -> None:
        service = VaultRevealService(_FakeVault())
        revealed = await service.reveal_text("Contact <PERSON_AABBCCDD> today.")
        self.assertIn("Jane VaultTest", revealed)
        self.assertNotIn("<PERSON_AABBCCDD>", revealed)


class TestStreamingVaultReveal(unittest.IsolatedAsyncioTestCase):
    async def test_feed_reveals_complete_token_in_one_chunk(self) -> None:
        streaming = StreamingVaultReveal(VaultRevealService(_FakeVault()))
        revealed = await streaming.feed("Contact <PERSON_AABBCCDD> today.")
        self.assertEqual(revealed, "Contact Jane VaultTest today.")

    async def test_feed_handles_token_split_across_chunks(self) -> None:
        streaming = StreamingVaultReveal(VaultRevealService(_FakeVault()))
        first = await streaming.feed("Contact <PERSON_AABB")
        second = await streaming.feed("CCDD> today.")
        self.assertEqual(first, "Contact ")
        self.assertEqual(second, "Jane VaultTest today.")

    async def test_feed_emits_plain_angle_brackets(self) -> None:
        streaming = StreamingVaultReveal(VaultRevealService(_FakeVault()))
        revealed = await streaming.feed("x < 5 and y")
        self.assertEqual(revealed, "x < 5 and y")

    async def test_flush_emits_incomplete_token_literal(self) -> None:
        streaming = StreamingVaultReveal(VaultRevealService(_FakeVault()))
        held = await streaming.feed("Contact <PERSON_AABB")
        flushed = await streaming.flush()
        self.assertEqual(held, "Contact ")
        self.assertEqual(flushed, "<PERSON_AABB")


if __name__ == "__main__":
    unittest.main()
