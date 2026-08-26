from __future__ import annotations

import re
from typing import Any

from pydantic import ValidationError

from agentic_shared.core.security.guard.injection import looks_like_prompt_injection
from agentic_shared.domains.annotations.models import ChunkComment

# Hungarian + English coarse terms (substring match, word boundaries where practical)
_OBSCENE_TERMS = frozenset(
    {
        "basz",
        "baszás",
        "baszott",
        "kurva",
        "kurvák",
        "picsa",
        "picsá",
        "fasz",
        "faszom",
        "faszfej",
        "geci",
        "szar",
        "szaros",
        "buzi",
        "ribanc",
        "fuck",
        "fucking",
        "fucker",
        "shit",
        "bitch",
        "asshole",
        "cunt",
        "dick",
        "pussy",
    }
)


def contains_obscene_language(text: str) -> bool:
    lowered = text.lower()
    tokens = re.findall(r"[\wáéíóöőúüű]+", lowered, flags=re.UNICODE)
    for token in tokens:
        if token in _OBSCENE_TERMS:
            return True
        for term in _OBSCENE_TERMS:
            if len(term) >= 4 and term in token:
                return True
    return False


__all__ = ["contains_obscene_language", "looks_like_prompt_injection", "normalize_comments"]


def normalize_comments(payload: dict[str, Any] | None) -> list[ChunkComment]:
    if not payload:
        return []
    raw = payload.get("comments")
    if not isinstance(raw, list):
        return []
    comments: list[ChunkComment] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            comments.append(ChunkComment.model_validate(item))
        except ValidationError:
            continue
    return comments
