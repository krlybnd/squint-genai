import type { PiiRedactionDetail, SearchMeta } from "../../api/types";

export interface ReasoningLine {
  step: string;
  message: string;
  status: "active" | "done";
  chunks?: number;
  piiRedactions?: number;
  piiDetails?: PiiRedactionDetail[];
  safeQuery?: string;
  checkpointId?: string;
  needsRetrieval?: boolean;
  searchQuery?: string;
  rewriteReason?: string;
  indexedDocumentCount?: number;
  searchMeta?: SearchMeta;
}

export interface ReasoningRun {
  id: string;
  at: string;
  query: string;
  lines: ReasoningLine[];
}
