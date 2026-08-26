from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


def payload_text(payload: Mapping[str, Any]) -> str:
    """Extract human-readable chunk text from a Qdrant/LlamaIndex payload."""
    if text := payload.get("text"):
        return str(text).strip()

    raw = payload.get("_node_content") or ""
    if not isinstance(raw, str) or not raw.strip():
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


def payload_page(payload: Mapping[str, Any]) -> str | int | None:
    page = payload.get("page")
    if isinstance(page, (str, int)):
        return page
    label = payload.get("page_label")
    if isinstance(label, (str, int)):
        return label
    return None
