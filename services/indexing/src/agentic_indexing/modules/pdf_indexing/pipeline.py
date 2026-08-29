import logging
import sys
import tempfile
from pathlib import Path

from agentic_shared.domains.retrieval.protocols.chunks import ChunkWriteRepository
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings
from llama_index.core import Settings as LISettings
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.schema import BaseNode, Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.readers.file import PDFReader

from agentic_indexing.modules.pdf_indexing.settings import get_module_settings

logger = logging.getLogger(__name__)


def materialize_nltk_cache() -> int:
    """Replace hardlinked NLTK files so pathsec can open them (Docker/uv layers)."""
    replaced = 0
    for entry in map(Path, sys.path):
        cache = entry / "llama_index" / "core" / "_static" / "nltk_cache"
        if not cache.is_dir():
            continue
        for path in cache.rglob("*"):
            if not path.is_file() or path.stat().st_nlink <= 1:
                continue
            data = path.read_bytes()
            path.unlink()
            path.write_bytes(data)
            replaced += 1
    return replaced


def _non_empty_nodes(nodes: list[BaseNode]) -> list[BaseNode]:
    return [node for node in nodes if node.get_content().strip()]


def _join_pdf_pages(
    docs: list[Document],
    *,
    doc_id: str,
    source_file: str,
    tenant_id: str,
) -> list[Document]:
    """Concatenate PDF pages so headings split across page breaks stay searchable.

    PDFReader emits one Document per page. Semantic split on each page in isolation
    drops queries like "Article I" when the heading is ``Article.`` on page N and
    ``I. Section. 1.`` on page N+1.
    """
    parts: list[str] = []
    page = None
    for index, doc in enumerate(docs):
        text = doc.get_content()
        if not text.strip():
            continue
        if page is None:
            page = doc.metadata.get("page_label", index + 1)
        parts.append(text)
    if not parts:
        return []
    return [
        Document(
            text="\n\n".join(parts),
            metadata={
                "doc_id": doc_id,
                "source_file": source_file,
                "tenant_id": tenant_id,
                "page": page,
            },
        )
    ]


def _attach_short_headings(nodes: list[BaseNode], *, max_heading_chars: int = 80) -> list[BaseNode]:
    """Keep isolated headings in the same chunk as the following body.

    Semantic split often isolates ``Article. I.`` from ``Section. 1. …``, so a query
    for "Article I" never hits the legislative-powers paragraph.
    """
    attached: list[BaseNode] = []
    heading: BaseNode | None = None
    for node in nodes:
        text = node.get_content().strip()
        if not text:
            continue
        if heading is not None:
            node.set_content(f"{heading.get_content().strip()}\n\n{text}")
            attached.append(node)
            heading = None
            continue
        if len(text) <= max_heading_chars:
            heading = node
            continue
        attached.append(node)
    if heading is not None:
        attached.append(heading)
    return attached


def index_pdf_bytes(
    pdf_bytes: bytes,
    *,
    doc_id: str,
    source_file: str,
    tenant_id: str,
    chunk_write: ChunkWriteRepository,
    llm: LLMSettings,
    embedding: EmbeddingSettings,
) -> int:
    """Semantic chunk PDF and upsert into Qdrant. Returns chunk count."""
    materialize_nltk_cache()
    module = get_module_settings()
    LISettings.embed_model = OpenAIEmbedding(
        model=embedding.embedding_model,
        api_base=llm.litellm_base_url,
        api_key=llm.proxy_api_key,
    )
    splitter = SemanticSplitterNodeParser(
        buffer_size=module.semantic_buffer_size,
        breakpoint_percentile_threshold=module.semantic_breakpoint_percentile_threshold,
        embed_model=LISettings.embed_model,
    )

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = Path(tmp.name)

    try:
        reader = PDFReader()
        docs = reader.load_data(file=tmp_path)
        joined = _join_pdf_pages(
            docs,
            doc_id=doc_id,
            source_file=source_file,
            tenant_id=tenant_id,
        )
        nodes = _non_empty_nodes(splitter.get_nodes_from_documents(joined)) if joined else []
        nodes = _attach_short_headings(nodes)
        if not nodes:
            logger.warning(
                "pdf produced no chunks doc_id=%s source_file=%s pages=%d",
                doc_id,
                source_file,
                len(docs),
            )
            return 0
        for node in nodes:
            node.metadata.setdefault("doc_id", doc_id)
            node.metadata.setdefault("source_file", source_file)
            node.metadata.setdefault("tenant_id", tenant_id)

        count = chunk_write.index_nodes(nodes, llm=llm, embedding=embedding)
        logger.info(
            "pdf indexed doc_id=%s source_file=%s chunks=%d tenant_id=%s",
            doc_id,
            source_file,
            count,
            tenant_id,
        )
        return count
    finally:
        tmp_path.unlink(missing_ok=True)
