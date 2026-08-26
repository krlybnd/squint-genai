import { apiBase, buildHeadersAsync } from "./http";
import i18n from "../i18n";
import type { ChunkComment, DocumentChunksResponse, IndexedDocument } from "./types";

export async function fetchDocumentChunks(
  sourceFile: string,
  docId?: string,
): Promise<DocumentChunksResponse> {
  const bySource = `${apiBase()}/v1/retrieval/documents/by-source/${encodeURIComponent(sourceFile)}/chunks`;
  const res = await fetch(bySource, { headers: await buildHeadersAsync(false) });
  if (res.ok) return res.json();

  if (docId) {
    const byDoc = `${apiBase()}/v1/retrieval/documents/${encodeURIComponent(docId)}/chunks`;
    const docRes = await fetch(byDoc, { headers: await buildHeadersAsync(false) });
    if (docRes.ok) return docRes.json();
  }
  throw new Error(`Failed to fetch document chunks (${res.status})`);
}

export async function fetchIndexedDocuments(): Promise<IndexedDocument[]> {
  const res = await fetch(`${apiBase()}/v1/retrieval/indexed-documents`, {
    headers: await buildHeadersAsync(false),
  });
  if (!res.ok) throw new Error(`Failed to fetch indexed documents (${res.status})`);
  return res.json();
}

export async function createChunkComment(
  chunkId: string,
  body: { selected_text: string; comment_text: string },
): Promise<ChunkComment> {
  const res = await fetch(`${apiBase()}/v1/annotations/chunks/${encodeURIComponent(chunkId)}/comments`, {
    method: "POST",
    headers: await buildHeadersAsync(),
    body: JSON.stringify(body),
  });
  if (res.status === 422) {
    const detail = await res.json().catch(() => ({}));
    const reason =
      typeof detail?.detail?.rejection_reason === "string"
        ? detail.detail.rejection_reason
        : i18n.t("annotations.rejection.default");
    throw new Error(reason);
  }
  if (!res.ok) throw new Error(`Failed to save comment (${res.status})`);
  return res.json();
}
