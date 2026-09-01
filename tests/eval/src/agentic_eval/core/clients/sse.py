"""Parse buffered chat SSE frames (OpenAPI types the body as ``text/event-stream`` string)."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from typing import Any

SseEvent = tuple[str, dict[str, Any]]

_VAULT_MARK = re.compile(r"\[\[vault:<[A-Z0-9_]+_[A-F0-9]{8}>\]\]([\s\S]*?)\[\[/vault\]\]")


def strip_vault_marks(text: str) -> str:
    """Drop UI vault wrappers; keep the plaintext the user sees."""
    return _VAULT_MARK.sub(r"\1", text)


def parse_sse(raw: str) -> list[SseEvent]:
    events: list[SseEvent] = []
    normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
    for block in normalized.split("\n\n"):
        if not block.strip():
            continue
        event = "message"
        data_line = ""
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data_line = line.split(":", 1)[1].strip()
        if not data_line:
            continue
        try:
            payload = json.loads(data_line)
        except json.JSONDecodeError:
            payload = {"raw": data_line}
        if isinstance(payload, dict):
            events.append((event, payload))
    return events


def answer_and_citations(events: Sequence[SseEvent]) -> tuple[str, list[dict[str, Any]]]:
    for event, payload in events:
        if event == "error":
            message = payload.get("message")
            raise RuntimeError(str(message) if message else "chat SSE error")
        if event != "done":
            continue
        answer = payload.get("answer")
        citations = payload.get("citations")
        return (
            strip_vault_marks(answer) if isinstance(answer, str) else "",
            citations if isinstance(citations, list) else [],
        )
    raise RuntimeError("chat SSE stream ended without a done event")
