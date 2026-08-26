import { apiBase, buildHeadersAsync } from "./http";
import type { ApiSchemas, Document } from "./types";

export async function fetchDocuments(): Promise<Document[]> {
  const res = await fetch(`${apiBase()}/v1/documents`, { headers: await buildHeadersAsync(false) });
  if (!res.ok) throw new Error("Failed to fetch documents");
  const data: ApiSchemas["DocumentListResponse"] = await res.json();
  return data.items ?? [];
}

export async function deleteDocument(documentId: string): Promise<void> {
  const res = await fetch(`${apiBase()}/v1/documents/${documentId}`, {
    method: "DELETE",
    headers: await buildHeadersAsync(false),
  });
  if (!res.ok) throw new Error(`Failed to delete document (${res.status})`);
}

export async function reindexDocument(documentId: string): Promise<Document> {
  const res = await fetch(`${apiBase()}/v1/documents/${documentId}/reindex`, {
    method: "POST",
    headers: await buildHeadersAsync(false),
  });
  if (!res.ok) throw new Error(`Failed to reindex document (${res.status})`);
  const data = (await res.json()) as { document: Document; job_id: string };
  return data.document;
}

export async function uploadDocument(file: File): Promise<void> {
  const presignRes = await fetch(`${apiBase()}/v1/documents/upload/presign`, {
    method: "POST",
    headers: await buildHeadersAsync(),
    body: JSON.stringify({ filename: file.name }),
  });
  if (!presignRes.ok) throw new Error(`Failed to get upload URL (${presignRes.status})`);

  const presign: ApiSchemas["PresignUploadResponse"] = await presignRes.json();

  const putRes = await fetch(presign.upload_url, {
    method: "PUT",
    headers: { ...(await buildHeadersAsync(false)), "Content-Type": presign.content_type ?? "application/pdf" },
    body: file,
  });
  if (!putRes.ok) throw new Error("Failed to upload file to storage");

  const completeRes = await fetch(
    `${apiBase()}/v1/documents/${presign.document.id}/complete`,
    {
      method: "POST",
      headers: await buildHeadersAsync(false),
    },
  );
  if (!completeRes.ok) {
    const detail = await completeRes.text().catch(() => "");
    throw new Error(`Failed to complete upload (${completeRes.status})${detail ? `: ${detail}` : ""}`);
  }
}
