import unittest
from unittest.mock import AsyncMock, MagicMock

from agentic_shared.domains.persistence.repositories.async_.pii_vault import (
    SqlAlchemyPiiVaultReadRepository,
)
from agentic_shared.domains.pii_vault.lookup import SqlAlchemyVaultTokenLookup
from agentic_shared.domains.pii_vault.query_service import QueryPiiTokenizationService
from agentic_shared.domains.pii_vault.query_spans import expand_adjacent_word_spans
from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
from agentic_shared.domains.pii_vault.tokenizer import PiiTokenizer, make_deterministic_token
from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity


class _FakeAnalyzer:
    def __init__(self, entities: list[AnalyzerEntity]) -> None:
        self._entities = entities

    async def analyze(self, text: str, *, language: str = "en") -> list[AnalyzerEntity]:
        return list(self._entities)


class _FakeExistence:
    def __init__(self, known: set[str]) -> None:
        self.known = known
        self.calls: list[list[str]] = []

    async def existing_tokens(self, tokens, *, tenant_id: str) -> frozenset[str]:
        self.calls.append(list(tokens))
        return frozenset(token for token in tokens if token in self.known)


class TestExpandAdjacentWordSpans(unittest.TestCase):
    def test_adds_left_word_for_person(self) -> None:
        text = "What is Esther Szabo tax"
        entities = [AnalyzerEntity(entity_type="PERSON", start=15, end=20, score=0.9)]
        expanded = expand_adjacent_word_spans(text, entities)
        spans = {(item.start, item.end) for item in expanded}
        self.assertEqual(text[15:20], "Szabo")
        self.assertEqual(text[8:20], "Esther Szabo")
        self.assertIn((15, 20), spans)
        self.assertIn((8, 20), spans)

    def test_skips_non_person(self) -> None:
        text = "id 12345678-1-23 here"
        entities = [AnalyzerEntity(entity_type="HU_TAX_NUMBER", start=3, end=16, score=0.9)]
        self.assertEqual(expand_adjacent_word_spans(text, entities), entities)


class TestQueryPiiTokenizationService(unittest.IsolatedAsyncioTestCase):
    async def test_replaces_only_vault_hits(self) -> None:
        text = "Ask Jane VaultTest please"
        known = make_deterministic_token(
            "PERSON", "Jane VaultTest", tenant_id="tenant-a", token_salt="salt"
        )
        service = QueryPiiTokenizationService(
            analyzer=_FakeAnalyzer(
                [AnalyzerEntity(entity_type="PERSON", start=4, end=18, score=0.9)]
            ),
            tokenizer=PiiTokenizer(token_salt="salt"),
            settings=PiiVaultSettings(_env_file=None, enabled=True),
            existence=_FakeExistence({known}),
        )
        replaced = await service.tokenize_query(text, tenant_id="tenant-a")
        self.assertIn(known, replaced)
        self.assertNotIn("Jane VaultTest", replaced)

    async def test_leaves_unknown_span_plaintext(self) -> None:
        text = "Ask Jane VaultTest please"
        service = QueryPiiTokenizationService(
            analyzer=_FakeAnalyzer(
                [AnalyzerEntity(entity_type="PERSON", start=4, end=18, score=0.9)]
            ),
            tokenizer=PiiTokenizer(token_salt="salt"),
            settings=PiiVaultSettings(_env_file=None, enabled=True),
            existence=_FakeExistence(set()),
        )
        replaced = await service.tokenize_query(text, tenant_id="tenant-a")
        self.assertEqual(replaced, text)
        self.assertNotIn("<PERSON_", replaced)

    async def test_expands_partial_person_when_full_name_is_in_vault(self) -> None:
        text = "What is Esther Szabo tax id"
        full = make_deterministic_token(
            "PERSON", "Esther Szabo", tenant_id="tenant-a", token_salt="salt"
        )
        service = QueryPiiTokenizationService(
            analyzer=_FakeAnalyzer(
                [AnalyzerEntity(entity_type="PERSON", start=15, end=20, score=0.9)]
            ),
            tokenizer=PiiTokenizer(token_salt="salt"),
            settings=PiiVaultSettings(_env_file=None, enabled=True),
            existence=_FakeExistence({full}),
        )
        replaced = await service.tokenize_query(text, tenant_id="tenant-a")
        self.assertIn(full, replaced)
        self.assertNotIn("Esther Szabo", replaced)

    async def test_skips_replace_without_existence_port(self) -> None:
        text = "Ask Jane VaultTest please"
        service = QueryPiiTokenizationService(
            analyzer=_FakeAnalyzer(
                [AnalyzerEntity(entity_type="PERSON", start=4, end=18, score=0.9)]
            ),
            tokenizer=PiiTokenizer(token_salt="salt"),
            settings=PiiVaultSettings(_env_file=None, enabled=True),
            existence=None,
        )
        replaced = await service.tokenize_query(text, tenant_id="tenant-a")
        self.assertEqual(replaced, text)

    async def test_maps_hungarian_name_order_to_indexed_person_token(self) -> None:
        text = "kicsoda Dr. Varga Levente?"
        start = text.index("Varga Levente")
        end = start + len("Varga Levente")
        indexed = make_deterministic_token(
            "PERSON", "Levente Varga", tenant_id="tenant-a", token_salt="salt"
        )

        class _Identity:
            async def token_for_equivalent_name(self, name: str, *, tenant_id: str) -> str | None:
                if name == "Varga Levente":
                    return indexed
                return None

        service = QueryPiiTokenizationService(
            analyzer=_FakeAnalyzer(
                [AnalyzerEntity(entity_type="PERSON", start=start, end=end, score=0.9)]
            ),
            tokenizer=PiiTokenizer(token_salt="salt"),
            settings=PiiVaultSettings(_env_file=None, enabled=True),
            existence=_FakeExistence(set()),
            person_identity=_Identity(),
        )
        replaced = await service.tokenize_query(text, tenant_id="tenant-a")
        self.assertIn(indexed, replaced)
        self.assertNotIn("Varga Levente", replaced)


class TestVaultTokenLookup(unittest.IsolatedAsyncioTestCase):
    async def test_existing_tokens_queries_tenant_and_token(self) -> None:
        result = MagicMock()
        result.scalars.return_value.all.return_value = ["<PERSON_AAAA0001>"]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)
        factory = MagicMock()
        factory.return_value.__aenter__ = AsyncMock(return_value=session)
        factory.return_value.__aexit__ = AsyncMock(return_value=False)
        lookup = SqlAlchemyVaultTokenLookup(factory)
        found = await lookup.existing_tokens(
            ["<PERSON_AAAA0001>", "<PERSON_DEADBEEF>"],
            tenant_id="tenant-a",
        )
        self.assertEqual(found, frozenset({"<PERSON_AAAA0001>"}))
        session.execute.assert_awaited_once()

    async def test_read_repo_existing_tokens_uses_bound_tenant(self) -> None:
        result = MagicMock()
        result.scalars.return_value.all.return_value = ["<PERSON_AAAA0001>"]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)
        repo = SqlAlchemyPiiVaultReadRepository(session, "tenant-a", cipher=MagicMock())
        found = await repo.existing_tokens(["<PERSON_AAAA0001>"])
        self.assertEqual(found, frozenset({"<PERSON_AAAA0001>"}))
        session.execute.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
