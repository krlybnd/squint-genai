from agentic_shared.domains.retrieval.models import IndexedDocumentEntry

from agentic_chat.core.nodes.rewrite.settings import get_module_settings


def _catalog_prompt_block(indexed: list[IndexedDocumentEntry]) -> str:
    limit = get_module_settings().indexed_catalog_limit
    if not indexed:
        return "No documents are currently indexed. Set needs_document_search=false."
    lines = [f"- {doc.source_file or '?'} ({doc.chunk_count} chunk)" for doc in indexed[:limit]]
    extra = f"\n… and {len(indexed) - limit} more" if len(indexed) > limit else ""
    return f"Currently indexed documents ({len(indexed)}):\n" + "\n".join(lines) + extra


def build_rewrite_router_system_prompt(*, indexed: list[IndexedDocumentEntry]) -> str:
    catalog_block = _catalog_prompt_block(indexed)
    return f"""You classify user messages for a document RAG agent (Adaptive RAG router).

{catalog_block}

Retrieval always searches with the user's original message. You only decide whether to
retrieve. Do not rewrite, translate, or keyword-ize the question.

Respond with a single JSON object only (no markdown):
{{
  "needs_document_search": boolean,
  "reason": string
}}

needs_document_search=false only for greetings, thanks, farewells, or questions about the
chat UI / the bot itself (hello, thanks, ki vagy, what can you do).
needs_document_search=true for every other message when documents are indexed — including
facts, papers, laws, missions, frameworks, and questions you could answer from memory.
Never skip retrieval so the model can answer from parametric knowledge.

Examples:
- "hello" → false
- "thanks" → false
- "What architecture does Attention Is All You Need propose?" → true
- "How does the Transformer encode token order without recurrence?" → true
"""
