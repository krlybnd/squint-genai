from __future__ import annotations

from pydantic import ValidationError

from agentic_shared.domains.annotations.models import ChunkComment


def normalize_comments(raw: object | None) -> list[ChunkComment]:
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
