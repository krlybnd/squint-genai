"""Retrieval tool catalog — docs for HTTP tools and query-routing LLM prompts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetrievalToolSpec:
    name: str
    summary: str
    parameters: str
    query_guidelines: str
    returns: str


SEARCH_DOCUMENTS = RetrievalToolSpec(
    name="search_documents",
    summary=(
        "Hybrid search (dense embedding + sparse BM25, RRF fusion) "
        "over indexed PDF chunks, optional rerank."
    ),
    parameters="query: str (required), top_k: int (optional, default 5, range 1–20)",
    query_guidelines="""
How to formulate `query` for best recall:
- Use short declarative keyword phrases, not conversational questions.
  Good (HU): "szerződés fizetési határidő késedelmi kamat"
  Good (EN): "Transformer attention heads d_k base model"
  Bad: "Mennyi a késedelmi kamat a szerződésben?"
- Include named entities: filenames, people, products, dates, section topics when known.
- One focused topic per call; split multi-part questions into separate searches.
- Keep the user's language. Match indexed filenames (English PDFs → English terms).
  Do not translate the query into another language.
- Avoid filler words (please, can you, tell me about).
- For summaries use broader terms; for facts use precise terms.
- For "what is in the document" / overview questions use: document title, main subject,
  chapter themes, author if known.
- top_k: 3–5 for narrow factual lookup, 8–12 for broad context.
""".strip(),
    returns="List of chunks: chunk_id, text, score, source_file, page, doc_id",
)

GET_SOURCE_CITATION = RetrievalToolSpec(
    name="get_source_citation",
    summary="Fetch citation metadata for a chunk returned by search_documents.",
    parameters="chunk_id: str (required) — exact chunk_id from search_documents",
    query_guidelines=(
        "Call after search_documents when you need page/section/excerpt for citations."
    ),
    returns="chunk_id, source_file, page, section, excerpt",
)

LIST_INDEXED_DOCUMENTS = RetrievalToolSpec(
    name="list_indexed_documents",
    summary="List indexed document sources currently available in the vector store.",
    parameters="(none)",
    query_guidelines=(
        "Use before search when unsure whether any PDFs are indexed, or to see filenames."
    ),
    returns="List of doc_id, source_file, chunk_count",
)

ALL_TOOLS: tuple[RetrievalToolSpec, ...] = (
    SEARCH_DOCUMENTS,
    GET_SOURCE_CITATION,
    LIST_INDEXED_DOCUMENTS,
)


def format_tool_doc(tool: RetrievalToolSpec) -> str:
    return f"""### {tool.name}
{tool.summary}

Parameters: {tool.parameters}

Query / usage guidelines:
{tool.query_guidelines}

Returns: {tool.returns}
"""


def format_retrieval_tools_prompt_for_query_rewrite() -> str:
    """Prompt block describing retrieval tools for the query-routing LLM."""
    parts = [
        "The retrieval layer exposes these tools. For document questions you must produce "
        "a `search_documents.query` string following the guidelines below.",
        "",
    ]
    parts.extend(format_tool_doc(t) for t in ALL_TOOLS)
    return "\n\n".join(parts)
