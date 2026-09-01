import unittest

from agentic_shared.domains.pii_vault.extra_recognizers import supplement_analyzer_entities
from agentic_shared.domains.pii_vault.reveal_service import (
    StreamingVaultReveal,
    VaultRevealService,
    collect_vault_tokens,
)
from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity


class TestExtraRecognizers(unittest.TestCase):
    def test_adds_hu_tax_number(self) -> None:
        text = "Tax id 12345678-1-23 applies."
        entities = supplement_analyzer_entities(text, [])
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].entity_type, "HU_TAX_NUMBER")

    def test_contract_rule_replaces_overlapping_analyzer_span(self) -> None:
        text = "12345678-1-23"
        existing = [AnalyzerEntity(entity_type="PHONE_NUMBER", start=0, end=len(text), score=0.4)]
        entities = supplement_analyzer_entities(text, existing)
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].entity_type, "HU_TAX_NUMBER")

    def test_contract_rule_drops_partial_analyzer_span(self) -> None:
        text = "Tax id 12345678-1-23 applies."
        existing = [AnalyzerEntity(entity_type="US_BANK_NUMBER", start=7, end=15, score=0.05)]
        entities = supplement_analyzer_entities(text, existing)
        self.assertEqual([entity.entity_type for entity in entities], ["HU_TAX_NUMBER"])
        self.assertEqual(text[entities[0].start : entities[0].end], "12345678-1-23")

    def test_spaced_iban_is_a_single_span(self) -> None:
        text = "IBAN HU68 KAMU 0001 2345 6789 0123 4567 confirmed."
        existing = [AnalyzerEntity(entity_type="DATE_TIME", start=30, end=39, score=0.85)]
        entities = supplement_analyzer_entities(text, existing)
        self.assertEqual([entity.entity_type for entity in entities], ["IBAN_CODE"])
        self.assertEqual(
            text[entities[0].start : entities[0].end],
            "HU68 KAMU 0001 2345 6789 0123 4567",
        )

    def test_unspaced_iban_still_matches(self) -> None:
        text = "IBAN HU68KAMU00012345678901234567 confirmed."
        entities = supplement_analyzer_entities(text, [])
        self.assertEqual([entity.entity_type for entity in entities], ["IBAN_CODE"])

    def test_keeps_analyzer_spans_that_do_not_overlap(self) -> None:
        text = "Levente Varga, tax id 12345678-1-23."
        existing = [AnalyzerEntity(entity_type="PERSON", start=0, end=13, score=0.85)]
        entities = supplement_analyzer_entities(text, existing)
        self.assertEqual(
            sorted(entity.entity_type for entity in entities),
            ["HU_TAX_NUMBER", "PERSON"],
        )


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

    async def test_reveal_text_marked_wraps_plaintext(self) -> None:
        service = VaultRevealService(_FakeVault())
        revealed = await service.reveal_text("Contact <PERSON_AABBCCDD> today.", marked=True)
        self.assertEqual(
            revealed,
            "Contact [[vault:<PERSON_AABBCCDD>]]Jane VaultTest[[/vault]] today.",
        )

    async def test_reveal_text_marked_wraps_copied_plaintext(self) -> None:
        service = VaultRevealService(_FakeVault())
        revealed = await service.reveal_text(
            "Contact Jane VaultTest today.",
            marked=True,
            extra_tokens=["<PERSON_AABBCCDD>"],
        )
        self.assertEqual(
            revealed,
            "Contact [[vault:<PERSON_AABBCCDD>]]Jane VaultTest[[/vault]] today.",
        )

    async def test_reveal_text_marked_matches_folded_plaintext(self) -> None:
        class _AccentVault:
            async def resolve_tokens(self, tokens):
                from agentic_shared.core.settings.secrets import SecuredStr

                return {"<PERSON_AABBCCDD>": SecuredStr("János Török")}

        service = VaultRevealService(_AccentVault())
        revealed = await service.reveal_text(
            "The CEO is Janos Torok of Kamuhold.",
            marked=True,
            extra_tokens=["<PERSON_AABBCCDD>"],
        )
        self.assertEqual(
            revealed,
            "The CEO is [[vault:<PERSON_AABBCCDD>]]Janos Torok[[/vault]] of Kamuhold.",
        )

    def test_collect_vault_tokens_walks_nested_retrieve_payload(self) -> None:
        tokens = collect_vault_tokens(
            {
                "retrieved_chunks": [{"page": 1, "body": "CEO <PERSON_AABBCCDD> signed."}],
                "search_meta": {"final_chunks": [{"excerpt": "Ask <ORG_11223344> later."}]},
            }
        )
        self.assertEqual(tokens, ["<ORG_11223344>", "<PERSON_AABBCCDD>"])


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

    async def test_feed_marked_emits_complete_span(self) -> None:
        streaming = StreamingVaultReveal(VaultRevealService(_FakeVault()), marked=True)
        first = await streaming.feed("Contact <PERSON_AABB")
        second = await streaming.feed("CCDD> today.")
        self.assertEqual(first, "Contact ")
        self.assertEqual(
            second,
            "[[vault:<PERSON_AABBCCDD>]]Jane VaultTest[[/vault]] today.",
        )


if __name__ == "__main__":
    unittest.main()
