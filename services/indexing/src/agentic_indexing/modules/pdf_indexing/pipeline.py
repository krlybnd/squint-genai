import logging
import sys
import tempfile
from pathlib import Path

from agentic_shared.infrastructure.vector.protocols import QdrantWriter
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings
from llama_index.core import Settings as LISettings
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.schema import BaseNode
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


def index_pdf_bytes(
    pdf_bytes: bytes,
    *,
    doc_id: str,
    source_file: str,
    tenant_id: str,
    qdrant_write: QdrantWriter,
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
        for i, doc in enumerate(docs):
            doc.metadata.update(
                {
                    "doc_id": doc_id,
                    "source_file": source_file,
                    "tenant_id": tenant_id,
                    "page": doc.metadata.get("page_label", i + 1),
                }
            )

        nodes = _non_empty_nodes(splitter.get_nodes_from_documents(docs))
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

        count = qdrant_write.index_nodes(nodes, llm=llm, embedding=embedding)
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
