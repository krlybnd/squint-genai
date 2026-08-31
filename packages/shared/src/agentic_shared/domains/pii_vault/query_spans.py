"""Widen NER spans by one adjacent word so query hashes can match index spans."""

from __future__ import annotations

import re

from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity

_WORD = re.compile(r"\S+")
_EXPAND_TYPES = frozenset({"PERSON"})


def expand_adjacent_word_spans(
    text: str,
    entities: list[AnalyzerEntity],
) -> list[AnalyzerEntity]:
    """Add one-word-left / one-word-right variants for PERSON spans.

    Index may store ``Esther Szabo`` while Presidio on a short query tags only
    ``Szabo``. The extra spans are hashed and kept only if the vault already
    has that token.
    """
    extra: list[AnalyzerEntity] = []
    for entity in entities:
        if entity.entity_type.strip().upper() not in _EXPAND_TYPES:
            continue
        left = _word_before(text, entity.start)
        right = _word_after(text, entity.end)
        score = min(1.0, entity.score + 0.01)
        entity_type = entity.entity_type
        if left is not None:
            extra.append(
                AnalyzerEntity(
                    entity_type=entity_type,
                    start=left[0],
                    end=entity.end,
                    score=score,
                )
            )
        if right is not None:
            extra.append(
                AnalyzerEntity(
                    entity_type=entity_type,
                    start=entity.start,
                    end=right[1],
                    score=score,
                )
            )
        if left is not None and right is not None:
            extra.append(
                AnalyzerEntity(
                    entity_type=entity_type,
                    start=left[0],
                    end=right[1],
                    score=score,
                )
            )
    return [*entities, *extra]


def _word_before(text: str, index: int) -> tuple[int, int] | None:
    prefix = text[:index]
    if not prefix or not prefix[-1].isspace():
        return None
    matches = list(_WORD.finditer(prefix))
    if not matches:
        return None
    match = matches[-1]
    return match.start(), match.end()


def _word_after(text: str, index: int) -> tuple[int, int] | None:
    if index >= len(text) or not text[index].isspace():
        return None
    match = _WORD.search(text, index)
    if match is None:
        return None
    return match.start(), match.end()


__all__ = ["expand_adjacent_word_spans"]
