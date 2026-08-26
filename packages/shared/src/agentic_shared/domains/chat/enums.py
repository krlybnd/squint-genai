from __future__ import annotations

from enum import StrEnum


class ChatMessageRole(StrEnum):
    """Persisted chat history / REST API (no system role)."""

    USER = "user"
    ASSISTANT = "assistant"

    @classmethod
    def from_stored(cls, role: str) -> ChatMessageRole:
        if role == cls.ASSISTANT:
            return cls.ASSISTANT
        return cls.USER


class LlmMessageRole(StrEnum):
    """OpenAI-style roles for chat completion requests."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
