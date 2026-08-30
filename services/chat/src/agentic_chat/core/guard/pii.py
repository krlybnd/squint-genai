"""Chat-local PII masking via analyzer + anonymizer clients."""

from __future__ import annotations

from dataclasses import dataclass

from agentic_shared.integrations.litellm.analyzer.protocols import Analyzer
from agentic_shared.integrations.litellm.anonymizer.protocols import Anonymizer

from agentic_chat.core.state import PiiDetail, PiiDetailState


@dataclass(frozen=True, slots=True)
class MaskedText:
    text: str
    count: int
    details: list[PiiDetailState]


async def mask_text(
    text: str,
    *,
    analyzer: Analyzer,
    anonymizer: Anonymizer,
    language: str = "en",
) -> MaskedText:
    if not text:
        return MaskedText(text="", count=0, details=[])
    entities = await analyzer.analyze(text, language=language)
    if not entities:
        return MaskedText(text=text, count=0, details=[])
    anonymized = await anonymizer.anonymize(text, entities)
    details = [
        PiiDetail(kind=e.entity_type, placeholder=f"<{e.entity_type}>").as_state() for e in entities
    ]
    return MaskedText(text=anonymized.text, count=len(entities), details=details)
