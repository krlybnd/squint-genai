"""Compare person names as the same identity, independent of word order."""

from __future__ import annotations

_TITLES = frozenset({"dr", "prof"})


def person_name_key(value: str) -> frozenset[str]:
    """Given + family name tokens. Order and titles are not part of identity."""
    parts: list[str] = []
    for raw in value.replace(",", " ").split():
        word = raw.strip(".:;").casefold()
        if word and word not in _TITLES:
            parts.append(word)
    return frozenset(parts)


def same_person_name(left: str, right: str) -> bool:
    """True when both sides name the same person (at least given + family)."""
    left_key = person_name_key(left)
    right_key = person_name_key(right)
    return len(left_key) >= 2 and left_key == right_key


__all__ = ["person_name_key", "same_person_name"]
