import { useCallback, useEffect, useRef, useState } from "react";
import {
  FileText,
  Upload,
  CheckCircle,
  Clock,
  Loader2,
  AlertCircle,
  Trash2,
  MoreVertical,
  RefreshCw,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { Document, deleteDocument, fetchDocuments, reindexDocument, uploadDocument } from "../api/client";
import { useAuth, useTenant } from "@are/ui-core";
import type { ChunkViewerTarget } from "../shared/types/chunks";
import { ChunkViewerModal } from "./ChunkViewerModal";
import "./DocumentsPanel.css";

type IndexStatus = Document["index_status"];

export function DocumentsPanel() {
  const { t } = useTranslation();
  const auth = useAuth();
  const { tenantId } = useTenant();
  const canWrite = auth.hasAnyRole("write", "admin");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [actionDocId, setActionDocId] = useState<string | null>(null);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [chunkViewer, setChunkViewer] = useState<ChunkViewerTarget | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    void tenantId;
    try {
      setDocuments(await fetchDocuments());
    } catch {
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  useEffect(() => {
    if (!openMenuId) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpenMenuId(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [openMenuId]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await uploadDocument(file);
      await load();
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleOpenDocument = (doc: Document) => {
    if (doc.index_status !== "indexed") return;
    setChunkViewer({ sourceFile: doc.filename, docId: doc.id });
  };

  const handleToggleMenu = (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setOpenMenuId((prev) => (prev === docId ? null : docId));
  };

  const handleDelete = async (doc: Document) => {
    if (!canWrite) return;
    setOpenMenuId(null);
    setActionDocId(doc.id);
    try {
      await deleteDocument(doc.id);
      await load();
    } finally {
      setActionDocId(null);
    }
  };

  const handleReindex = async (doc: Document) => {
    if (!canWrite) return;
    setOpenMenuId(null);
    setActionDocId(doc.id);
    try {
      await reindexDocument(doc.id);
      await load();
    } finally {
      setActionDocId(null);
    }
  };

  const canReindex = (status: IndexStatus | undefined) =>
    status === "indexed" || status === "failed" || status === "indexing";

  const statusLabel = (status: IndexStatus | undefined) => {
    switch (status) {
      case "indexed":
        return { className: "indexed", icon: <CheckCircle size={14} />, text: t("documents.indexed") };
      case "indexing":
        return { className: "indexing", icon: <Loader2 size={14} className="spin" />, text: t("documents.indexing") };
      case "failed":
        return { className: "failed", icon: <AlertCircle size={14} />, text: t("documents.failed") };
      default:
        return { className: "pending", icon: <Clock size={14} />, text: t("documents.pending") };
    }
  };

  return (
    <div className="documents-panel">
      <div className="panel-header">
        <h2>
          <FileText size={20} /> {t("documents.title")}
        </h2>
        <div className="panel-header-actions">
          {canWrite && (
            <>
              <button
                className="btn-upload"
                onClick={() => fileRef.current?.click()}
                disabled={uploading}
              >
                {uploading ? <Loader2 size={16} className="spin" /> : <Upload size={16} />}
                {t("documents.upload")}
              </button>
              <input ref={fileRef} type="file" accept=".pdf" hidden onChange={handleUpload} />
            </>
          )}
        </div>
      </div>

      <div className="doc-list">
        {loading && (
          <div className="doc-empty">
            <Loader2 size={24} className="spin" />
          </div>
        )}
        {!loading && documents.length === 0 && (
          <div className="doc-empty">
            <FileText size={32} strokeWidth={1.5} />
            <p>{t("documents.empty")}</p>
            <span>{canWrite ? t("documents.emptyHintWrite") : t("documents.emptyHintRead")}</span>
          </div>
        )}
        {documents.map((doc) => {
          const status = statusLabel(doc.index_status);
          const menuOpen = openMenuId === doc.id;
          const actionBusy = actionDocId === doc.id;
          return (
            <div
              key={doc.id}
              className={`doc-card ${doc.index_status === "indexed" ? "doc-card-clickable" : ""}`}
              role={doc.index_status === "indexed" ? "button" : undefined}
              tabIndex={doc.index_status === "indexed" ? 0 : undefined}
              onClick={() => handleOpenDocument(doc)}
              onKeyDown={(e) => {
                if (doc.index_status === "indexed" && (e.key === "Enter" || e.key === " ")) {
                  e.preventDefault();
                  handleOpenDocument(doc);
                }
              }}
            >
              <div className="doc-icon">
                <FileText size={20} />
              </div>
              <div className="doc-info">
                <span className="doc-name">{doc.filename}</span>
                <span className="doc-meta">
                  {doc.page_count ? t("documents.pages", { count: doc.page_count }) : ""}
                  {new Date(doc.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className={`doc-status ${status.className}`}>
                {status.icon} {status.text}
              </div>
              {canWrite && (
                <div
                  className="doc-actions"
                  ref={menuOpen ? menuRef : undefined}
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    className="btn-doc-actions"
                    title={t("documents.actions")}
                    disabled={actionBusy}
                    onClick={(e) => handleToggleMenu(doc.id, e)}
                  >
                    {actionBusy ? (
                      <Loader2 size={14} className="spin" />
                    ) : (
                      <MoreVertical size={14} />
                    )}
                  </button>
                  {menuOpen && (
                    <div className="doc-actions-menu">
                      <button
                        type="button"
                        disabled={!canReindex(doc.index_status)}
                        onClick={() => handleReindex(doc)}
                      >
                        <RefreshCw size={14} />
                        {t("documents.revectorization")}
                      </button>
                      <button type="button" className="danger" onClick={() => handleDelete(doc)}>
                        <Trash2 size={14} />
                        {t("documents.delete")}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {chunkViewer && (
        <ChunkViewerModal
          sourceFile={chunkViewer.sourceFile}
          docId={chunkViewer.docId}
          canWrite={canWrite}
          onClose={() => setChunkViewer(null)}
        />
      )}
    </div>
  );
}
