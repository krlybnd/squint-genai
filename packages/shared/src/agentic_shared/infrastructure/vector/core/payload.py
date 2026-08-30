from __future__ import annotations

import json

from agentic_shared.infrastructure.vector.core.types import VectorPayload


def payload_text(payload: VectorPayload) -> str:
    """Extract human-readable chunk text from a Qdrant/LlamaIndex payload."""
    if payload.text:
        return payload.text.strip()

    raw = payload.node_content or ""
    if not raw.strip():
        return ""

    if raw.lstrip().startswith("{"):
        try:
            node = json.loads(raw)
        except json.JSONDecodeError:
            return raw.strip()
        if isinstance(node, dict):
            text = node.get("text")
            if text:
                return str(text).strip()
    return raw.strip()


def payload_page(payload: VectorPayload) -> str | int | None:
    if payload.page is not None:
        return payload.page
    return payload.page_label
