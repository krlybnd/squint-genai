from __future__ import annotations

from enum import StrEnum


class AgentGraphNode(StrEnum):
    PLAN = "plan"
    GUARD = "guard"
    BLOCK = "block"
    REWRITE = "rewrite"
    RETRIEVE = "retrieve"
    GENERATE = "generate"

    @classmethod
    def from_stream_name(cls, name: str) -> AgentGraphNode | None:
        try:
            return cls(name)
        except ValueError:
            return None
