"""Contract-oriented regex supplements on top of Presidio analyzer spans."""

from __future__ import annotations

import re
from dataclasses import dataclass

from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity

_HU_TAX_NUMBER = re.compile(r"\b\d{8}-\d-\d{2}\b")
_HU_COMPANY_REG = re.compile(r"\b\d{2}-\d{2}-\d{6}\b")
_HU_IBAN = re.compile(r"\bHU\d{2}[A-Z0-9]{23}\b", re.IGNORECASE)


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


def _overlaps(start: int, end: int, entities: list[AnalyzerEntity]) -> bool:
    for entity in entities:
        if start < entity.end and end > entity.start:
            return True
    return False


def supplement_analyzer_entities(
    text: str,
    entities: list[AnalyzerEntity],
) -> list[AnalyzerEntity]:
    """Add HU/contract regex hits Presidio may miss."""
    merged = list(entities)
    for rule in _CONTRACT_RULES:
        for match in rule.pattern.finditer(text):
            start, end = match.span()
            if _overlaps(start, end, merged):
                continue
            merged.append(
                AnalyzerEntity(
                    entity_type=rule.entity_type,
                    start=start,
                    end=end,
                    score=rule.score,
                )
            )
    return merged


__all__ = ["supplement_analyzer_entities"]
