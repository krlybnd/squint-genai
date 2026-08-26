import json
from datetime import datetime
from typing import Self
from uuid import UUID

from agentic_shared.domains.chat.roles import ChatMessageRole
from agentic_shared.domains.persistence.entities import ChatMessage
from agentic_shared.domains.retrieval.models import ChunkCitation
from pydantic import BaseModel, Field, ValidationError

from agentic_chat.core.state import GraphMessage, graph_message


class CitationOut(BaseModel):
    chunk_id: str = ""
    doc_id: str = ""
    source_file: str = ""
    page: int | str | None = None
    excerpt: str = ""

    @classmethod
    def from_citation(cls, citation: ChunkCitation) -> Self:
        return cls.model_validate(citation.model_dump())

    @classmethod
    def from_stored(cls, raw: object) -> Self | None:
        if not isinstance(raw, dict):
            return None
        try:
            return cls.from_citation(ChunkCitation.model_validate(raw))
        except ValidationError:
            return None

    @classmethod
    def list_from_stored(cls, raw_list: object) -> list[Self]:
        if not isinstance(raw_list, list):
            return []
        out: list[Self] = []
        for item in raw_list:
            parsed = cls.from_stored(item)
            if parsed is not None:
                out.append(parsed)
        return out


def citations_from_json(citations_json: str | None) -> list[CitationOut]:
    if not citations_json:
        return []
    return CitationOut.list_from_stored(json.loads(citations_json))


class ChatMessageOut(BaseModel):
    id: UUID
    role: ChatMessageRole
    content: str
    citations: list[CitationOut] = Field(default_factory=list)
    created_at: datetime

    @classmethod
    def from_entity(cls, entity: ChatMessage) -> Self:
        return cls(
            id=entity.id,
            role=ChatMessageRole.from_stored(entity.role),
            content=entity.content,
            citations=citations_from_json(entity.citations_json),
            created_at=entity.created_at,
        )


def to_graph_messages(messages: list[ChatMessageOut]) -> list[GraphMessage]:
    return [graph_message(m.role, m.content) for m in messages]


class ChatSessionOut(BaseModel):
    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateSessionRequest(BaseModel):
    title: str | None = None


class ChatStreamRequest(BaseModel):
    message: str = Field(min_length=1)
    run_id: str | None = Field(default=None, min_length=1)


class ChatReplayRequest(BaseModel):
    run_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    checkpoint_id: str | None = None
