from __future__ import annotations

from typing import TypedDict


class ChunkPointPayload(TypedDict, total=False):
    point_type: str
    tenant_id: str
    doc_id: str
    source_file: str
    page: str | int
    page_label: str | int
    text: str


class CommentPointPayload(TypedDict, total=False):
    point_type: str
    comment_id: str
    parent_chunk_id: str
    tenant_id: str
    selected_text: str
    comment_text: str
    text: str
    user_id: str | None
    created_at: str
    doc_id: str | None
    source_file: str | None
    page: str | int | None
