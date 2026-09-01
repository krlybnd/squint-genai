import unittest

from agentic_shared.core.settings.secrets import SecuredStr
from agentic_shared.crosscut.crypto.cipher import FernetCipher
from agentic_shared.crosscut.crypto.settings import CryptoSettings
from agentic_shared.domains.pii_vault.tokenizer import PiiTokenizer, make_deterministic_token
from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity


class TestFernetCipher(unittest.TestCase):
    def setUp(self) -> None:
        self.cipher = FernetCipher(CryptoSettings(_env_file=None))

    def test_encrypt_decrypt_round_trip(self) -> None:
        plaintext = SecuredStr("Jane VaultTest")
        ciphertext = self.cipher.encrypt(plaintext)
        self.assertNotEqual(ciphertext, plaintext.get_secret_value())
        self.assertEqual(self.cipher.decrypt(ciphertext).get_secret_value(), "Jane VaultTest")

    def test_encrypt_accepts_plain_str(self) -> None:
        ciphertext = self.cipher.encrypt("Jane VaultTest")
        self.assertEqual(self.cipher.decrypt(ciphertext).get_secret_value(), "Jane VaultTest")


class TestDeterministicToken(unittest.TestCase):
    def test_same_value_same_token(self) -> None:
        token_a = make_deterministic_token(
            "PERSON",
            "Jane VaultTest",
            tenant_id="tenant-a",
            token_salt="salt",
        )
        token_b = make_deterministic_token(
            "PERSON",
            "  jane vaulttest  ",
            tenant_id="tenant-a",
            token_salt="salt",
        )
        self.assertEqual(token_a, token_b)
        self.assertTrue(token_a.startswith("<PERSON_"))

    def test_different_tenant_different_token(self) -> None:
        token_a = make_deterministic_token(
            "EMAIL_ADDRESS",
            "vault-test@example.com",
            tenant_id="tenant-a",
            token_salt="salt",
        )
        token_b = make_deterministic_token(
            "EMAIL_ADDRESS",
            "vault-test@example.com",
            tenant_id="tenant-b",
            token_salt="salt",
        )
        self.assertNotEqual(token_a, token_b)


class TestPiiTokenizer(unittest.TestCase):
    def setUp(self) -> None:
        self.tokenizer = PiiTokenizer(token_salt="salt")

    def test_replaces_spans_with_tokens(self) -> None:
        text = "Contact Jane VaultTest at vault-test@example.com."
        entities = [
            AnalyzerEntity(entity_type="PERSON", start=8, end=22, score=0.9),
            AnalyzerEntity(entity_type="EMAIL_ADDRESS", start=26, end=48, score=0.99),
        ]
        result = self.tokenizer.tokenize(text, entities, tenant_id="default")
        self.assertNotIn("Jane VaultTest", result.text)
        self.assertNotIn("vault-test@example.com", result.text)
        self.assertIn("<PERSON_", result.text)
        self.assertIn("<EMAIL_ADDRESS_", result.text)
        self.assertEqual(result.entity_count, 2)
        self.assertEqual(result.unique_token_count, 2)
        self.assertEqual(len(result.entries), 2)
        self.assertNotIn("Jane VaultTest", repr(result.entries[0]))

    def test_entry_draft_masks_plaintext_in_repr(self) -> None:
        text = "Jane VaultTest"
        entities = [AnalyzerEntity(entity_type="PERSON", start=0, end=len(text), score=0.9)]
        result = self.tokenizer.tokenize(text, entities, tenant_id="default")
        rendered = repr(result.entries[0])
        self.assertNotIn("Jane VaultTest", rendered)
        self.assertEqual(result.entries[0].plaintext.get_secret_value(), "Jane VaultTest")

    def test_overlapping_spans_keep_higher_score(self) -> None:
        text = "Jane VaultTest"
        entities = [
            AnalyzerEntity(entity_type="PERSON", start=0, end=4, score=0.5),
            AnalyzerEntity(entity_type="PERSON", start=0, end=14, score=0.95),
        ]
        result = self.tokenizer.tokenize(text, entities, tenant_id="default")
        self.assertEqual(result.entity_count, 1)
        self.assertNotIn("Jane", result.text)
        self.assertTrue(result.text.startswith("<PERSON_"))

    def test_iter_candidates_does_not_collapse_overlaps(self) -> None:
        text = "Esther Szabo"
        entities = [
            AnalyzerEntity(entity_type="PERSON", start=7, end=12, score=0.9),
            AnalyzerEntity(entity_type="PERSON", start=0, end=12, score=0.91),
        ]
        candidates = self.tokenizer.iter_candidates(text, entities, tenant_id="tenant-a")
        self.assertEqual(len(candidates), 2)

    def test_apply_vault_hits_keeps_longest_span(self) -> None:
        text = "Ask Esther Szabo today"
        full = make_deterministic_token("PERSON", "Esther Szabo", tenant_id="t", token_salt="salt")
        last = make_deterministic_token("PERSON", "Szabo", tenant_id="t", token_salt="salt")
        from agentic_shared.domains.pii_vault.models import TokenCandidate

        replaced = self.tokenizer.apply_vault_hits(
            text,
            [
                TokenCandidate(start=11, end=16, token=last, entity_type="PERSON"),
                TokenCandidate(start=4, end=16, token=full, entity_type="PERSON"),
            ],
        )
        self.assertIn(full, replaced)
        self.assertNotIn("Esther", replaced)
        self.assertNotIn(last, replaced)


if __name__ == "__main__":
    unittest.main()
