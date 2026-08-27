"""Shared eval contracts — no base classes; modules implement these."""

from __future__ import annotations

from typing import Protocol

from agentic_chat.core.deps import AgentGraphDeps


class HostStack(Protocol):
    """Chat stack as reached from the eval process (suite ``SutSettings``)."""

    openai_compatible_base_url: str
    proxy_api_key: str

    def to_graph_deps(self, *, top_k: int | None = None) -> AgentGraphDeps: ...
