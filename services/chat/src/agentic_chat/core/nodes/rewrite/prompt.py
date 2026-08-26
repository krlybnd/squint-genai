from agentic_shared.domains.retrieval.models import IndexedDocumentEntry
from agentic_shared.domains.retrieval.tool_catalog import (
    format_retrieval_tools_prompt_for_query_rewrite,
)

from agentic_chat.core.nodes.rewrite.settings import get_module_settings


def _catalog_prompt_block(indexed: list[IndexedDocumentEntry]) -> str:
    limit = get_module_settings().indexed_catalog_limit
    if not indexed:
        return "No documents are currently indexed in the vector store."
    lines = [f"- {doc.source_file or '?'} ({doc.chunk_count} chunk)" for doc in indexed[:limit]]
    extra = f"\n… and {len(indexed) - limit} more" if len(indexed) > limit else ""
    return (
        f"Currently indexed documents ({len(indexed)}):\n"
        + "\n".join(lines)
        + extra
        + "\n\nWhen indexed documents exist, prefer needs_document_search=true for substantive "
        "questions whose answer should come from uploaded files (definitions, facts, summaries, "
        "processes, policies, «mi?», «mit jelent?», «what is…?»). "
        "Do not force document search for pure social or meta messages."
    )


def build_rewrite_router_system_prompt(*, indexed: list[IndexedDocumentEntry]) -> str:
    catalog_block = _catalog_prompt_block(indexed)
    tool_docs = format_retrieval_tools_prompt_for_query_rewrite()
    return f"""You are a query router for a document RAG agent that calls retrieval tools.

{tool_docs}

{catalog_block}

Classify the user message and, when document search is needed, rewrite it into an optimal
`search_documents` query following the guidelines above.

Respond with a single JSON object only (no markdown):
{{
  "needs_document_search": boolean,
  "search_query": string,
  "reason": string
}}

Intent rules:
- needs_document_search=false for purely conversational messages: greetings, farewells, thanks,
  acknowledgements, small talk, jokes, or explicit meta questions about the chat UI or bot
  (e.g. «ki vagy?», «mit tudsz?», «hello», «thanks», «ok»).
- needs_document_search=true when the user asks about uploaded/indexed files, PDFs, internal docs,
  or any substantive question that should be answered from the knowledge base — including broad
  questions like «mi van a dokumentumban?» / «summarize the PDF» when documents are indexed.
- When indexed documents exist, do NOT treat factual or explanatory questions as conversational
  just because they are short. Only skip search when the message has no document-related intent.
- search_query: empty when needs_document_search is false; otherwise the optimized search query
  (same language as the user unless documents are clearly English-only).
- reason: one short sentence in the user's language explaining the routing decision.
"""
