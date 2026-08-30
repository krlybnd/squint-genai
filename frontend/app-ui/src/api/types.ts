import type { ApiComponents, ChatComponents } from "./generated";

type ApiSchemas = ApiComponents["schemas"];
type ChatSchemas = ChatComponents["schemas"];

export type Document = ApiSchemas["DocumentOut"];
export type ChatSession = ChatSchemas["ChatSessionOut"];
export type ChatMessage = ChatSchemas["ChatMessageOut"];
export type Citation = ChatSchemas["CitationOut"] & { doc_id?: string };

export type DocumentChunk = {
  chunk_id: string;
  text: string;
  doc_id?: string | null;
  source_file?: string | null;
  page?: number | string | null;
  comments?: ChunkComment[];
};

export type ChunkComment = {
  comment_id: string;
  chunk_id?: string;
  selected_text: string;
  comment_text: string;
  user_id?: string | null;
  created_at?: string;
};

export type DocumentChunksResponse = {
  doc_id: string;
  source_file?: string | null;
  chunks: DocumentChunk[];
};

export type IndexedDocument = {
  doc_id: string;
  source_file: string;
  chunk_count: number;
};

export type PiiRedactionDetail = {
  kind: string;
  placeholder: string;
};

export type ChunkPreview = {
  chunk_id: string;
  source_file?: string | null;
  page?: number | string | null;
  score?: number | null;
  excerpt?: string;
  rank?: number;
  selected?: boolean;
};

export type SearchMeta = {
  query?: string;
  search_query?: string;
  search_type?: string;
  dense?: boolean;
  sparse?: boolean;
  fusion?: string;
  dense_model?: string;
  sparse_model?: string;
  candidate_top_k?: number;
  final_top_k?: number;
  candidates_found?: number;
  results_count?: number;
  skipped?: boolean;
  reason?: string;
  error?: string;
  rrf_candidates?: ChunkPreview[];
  final_chunks?: ChunkPreview[];
};

export type StreamEvent =
  | { type: "run"; run_id: string; replay?: boolean }
  | { type: "status"; step: string; chunks?: number }
  | {
      type: "reasoning";
      step: string;
      message: string;
      status: "active" | "done";
      chunks?: number;
      pii_redactions?: number;
      pii_details?: PiiRedactionDetail[];
      safe_query?: string;
      checkpoint_id?: string;
      needs_retrieval?: boolean;
      search_query?: string;
      rewrite_reason?: string;
      indexed_document_count?: number;
      search_meta?: SearchMeta;
    }
  | { type: "token"; content: string }
  | { type: "session"; session_id: string; title: string }
  | { type: "done"; answer: string; citations: Citation[] }
  | { type: "cancelled" }
  | { type: "error"; message: string };

export type { ApiSchemas, ChatSchemas };
