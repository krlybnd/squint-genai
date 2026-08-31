"""Contract-oriented regex supplements on top of Presidio analyzer spans."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity

_HU_TAX_NUMBER = re.compile(r"\b\d{8}-\d-\d{2}\b")
_HU_COMPANY_REG = re.compile(r"\b\d{2}-\d{2}-\d{6}\b")
# HU IBAN is HU + 2 check digits + a 24 character BBAN, usually printed in groups of four.
_HU_IBAN = re.compile(r"\bHU\d{2}(?:[ ]?[A-Z0-9]{4}){6}\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class _RegexEntityRule:
    entity_type: str
    pattern: re.Pattern[str]
    score: float


_CONTRACT_RULES: tuple[_RegexEntityRule, ...] = (
    _RegexEntityRule("HU_TAX_NUMBER", _HU_TAX_NUMBER, 0.9),
    _RegexEntityRule("HU_COMPANY_REG", _HU_COMPANY_REG, 0.85),
    _RegexEntityRule("IBAN_CODE", _HU_IBAN, 0.95),
)


def _overlaps(start: int, end: int, entities: Sequence[AnalyzerEntity]) -> bool:
    for entity in entities:
        if start < entity.end and end > entity.start:
            return True
    return False


def supplement_analyzer_entities(
    text: str,
    entities: list[AnalyzerEntity],
) -> list[AnalyzerEntity]:
    """Add HU/contract regex hits, dropping the analyzer spans they overlap.

    The generic recognizers routinely claim a fragment of a Hungarian identifier — the
    leading eight digits of a tax number, a group of four inside an IBAN — which would
    split one value across a token and some leftover plaintext. The contract rules know
    the full shape, so they win the span and each identifier stays a single token.
    """
    contract_hits = [
        AnalyzerEntity(
            entity_type=rule.entity_type,
            start=match.start(),
            end=match.end(),
            score=rule.score,
        )
        for rule in _CONTRACT_RULES
        for match in rule.pattern.finditer(text)
    ]
    if not contract_hits:
        return list(entities)
    kept = [entity for entity in entities if not _overlaps(entity.start, entity.end, contract_hits)]
    return kept + contract_hits


__all__ = ["supplement_analyzer_entities"]
