import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Loader2, MessageSquarePlus } from "lucide-react";
import { useTranslation } from "react-i18next";
import {
  createChunkComment,
  fetchDocumentChunks,
  type ChunkComment,
  type DocumentChunk,
} from "../api/client";
import { Modal, sanitizeText } from "@are/ui-core";
import "./ChunkViewerModal.css";

interface Props {
  docId?: string;
  sourceFile: string;
  initialChunkId?: string;
  canWrite?: boolean;
  onClose: () => void;
}

const PREVIEW_LEN = 80;

interface HighlightRange {
  start: number;
  end: number;
  commentId: string;
}

function findHighlightRanges(text: string, comments: ChunkComment[]): HighlightRange[] {
  const ranges: HighlightRange[] = [];
  for (const comment of comments) {
    const needle = comment.selected_text?.trim();
    if (!needle) continue;
    let from = 0;
    while (from < text.length) {
      const idx = text.indexOf(needle, from);
      if (idx === -1) break;
      ranges.push({
        start: idx,
        end: idx + needle.length,
        commentId: comment.comment_id,
      });
      from = idx + needle.length;
    }
  }
  return ranges.sort((a, b) => a.start - b.start || a.end - b.end);
}

function mergeHighlightRanges(ranges: HighlightRange[]): HighlightRange[] {
  const merged: HighlightRange[] = [];
  for (const range of ranges) {
    const last = merged[merged.length - 1];
    if (last && range.start < last.end) continue;
    merged.push(range);
  }
  return merged;
}

function renderCommentedText(
  text: string,
  comments: ChunkComment[],
  activeCommentId: string | null,
  commentedTitle: string,
) {
  if (!text) return "—";
  const byId = new Map(comments.map((c) => [c.comment_id, c]));
  const ranges = mergeHighlightRanges(findHighlightRanges(text, comments));
  if (ranges.length === 0) return sanitizeText(text);

  const parts: ReactNode[] = [];
  let cursor = 0;
  for (const range of ranges) {
    if (range.start > cursor) {
      parts.push(
        <span key={`plain-${cursor}`}>{sanitizeText(text.slice(cursor, range.start))}</span>,
      );
    }
    const comment = byId.get(range.commentId);
    parts.push(
      <mark
        key={`hl-${range.commentId}-${range.start}`}
        className={`chunk-comment-highlight${activeCommentId === range.commentId ? " active" : ""}`}
        title={comment?.comment_text?.trim() || commentedTitle}
      >
        {sanitizeText(text.slice(range.start, range.end))}
      </mark>,
    );
    cursor = range.end;
  }
  if (cursor < text.length) {
    parts.push(<span key={`plain-${cursor}`}>{sanitizeText(text.slice(cursor))}</span>);
  }
  return parts;
}

function chunkPreview(text: string): string {
  const cleaned = text.replace(/\s+/g, " ").trim();
  if (!cleaned) return "—";
  if (cleaned.length <= PREVIEW_LEN) return cleaned;
  return `${cleaned.slice(0, PREVIEW_LEN).trim()}…`;
}

export function ChunkViewerModal({
  docId,
  sourceFile,
  initialChunkId,
  canWrite = false,
  onClose,
}: Props) {
  const { t } = useTranslation();
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [index, setIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedText, setSelectedText] = useState("");
  const [commentDraft, setCommentDraft] = useState("");
  const [commentError, setCommentError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [activeCommentId, setActiveCommentId] = useState<string | null>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const textRef = useRef<HTMLElement>(null);
  const composeRef = useRef<HTMLDivElement>(null);
  const commentInputRef = useRef<HTMLTextAreaElement>(null);

  const loadChunks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDocumentChunks(sourceFile, docId);
      const sorted = [...data.chunks];
      setChunks(sorted);
      const start = initialChunkId
        ? sorted.findIndex((c) => c.chunk_id === initialChunkId)
        : 0;
      setIndex(start >= 0 ? start : 0);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [sourceFile, docId, initialChunkId]);

  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  useEffect(() => {
    void loadChunks();
  }, [loadChunks]);

  useEffect(() => {
    setSelectedText("");
    setCommentDraft("");
    setCommentError("");
    setActiveCommentId(null);
  }, [index]);

  useEffect(() => {
    itemRefs.current[index]?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [index, chunks.length]);

  useEffect(() => {
    if (!selectedText) return;
    composeRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    commentInputRef.current?.focus({ preventScroll: true });
  }, [selectedText]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLTextAreaElement) return;
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setIndex((i) => Math.max(0, i - 1));
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setIndex((i) => Math.min(chunks.length - 1, i + 1));
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [chunks.length]);

  const selectIndex = useCallback((i: number) => setIndex(i), []);

  const handleTextSelection = () => {
    if (!canWrite || !textRef.current) return;
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) {
      setSelectedText("");
      return;
    }
    const range = sel.getRangeAt(0);
    if (!textRef.current.contains(range.commonAncestorContainer)) {
      setSelectedText("");
      return;
    }
    const text = sel.toString().trim();
    setSelectedText(text);
    if (text) setCommentError("");
  };

  const handleSubmitComment = async () => {
    if (!canWrite || !current?.chunk_id || !selectedText || !commentDraft.trim()) return;
    setSubmitting(true);
    setCommentError("");
    try {
      const saved = await createChunkComment(current.chunk_id, {
        selected_text: selectedText,
        comment_text: commentDraft.trim(),
      });
      setChunks((prev) =>
        prev.map((c, i) =>
          i === index
            ? {
                ...c,
                comments: [...(c.comments ?? []), saved],
              }
            : c,
        ),
      );
      setCommentDraft("");
      setSelectedText("");
      window.getSelection()?.removeAllRanges();
    } catch (err) {
      setCommentError(
        err instanceof Error ? err.message : t("chunkViewer.saveCommentFailed"),
      );
    } finally {
      setSubmitting(false);
    }
  };

  const current = chunks[index];
  const fileLabel = sourceFile || current?.source_file || t("chunkViewer.defaultTitle");
  const comments: ChunkComment[] = current?.comments ?? [];

  const subtitleParts: string[] = [];
  if (!loading && chunks.length > 0) {
    subtitleParts.push(t("chunkViewer.meta", { count: chunks.length }));
    if (current?.page != null) {
      subtitleParts.push(t("chunkViewer.pageLabel", { page: current.page }));
    }
    if (canWrite) {
      subtitleParts.push(t("chunkViewer.selectHint"));
    }
  }
  const subtitle = subtitleParts.length > 0 ? subtitleParts.join(" · ") : undefined;

  return (
    <Modal
      open
      title={sanitizeText(fileLabel)}
      subtitle={subtitle}
      size="full"
      padded={false}
      onClose={onClose}
    >
      <div className="chunk-modal-split">
        <section className="chunk-modal-reader" aria-label={t("chunkViewer.readerLabel")}>
          {loading && (
            <div className="chunk-modal-loading">
              <Loader2 size={28} className="spin" />
              <span>{t("chunkViewer.loading")}</span>
            </div>
          )}
          {!loading && error && <p className="chunk-modal-error">{sanitizeText(error)}</p>}
          {!loading && !error && chunks.length === 0 && (
            <p className="chunk-modal-empty">{t("chunkViewer.empty")}</p>
          )}
          {!loading && !error && current && (
            <>
              <div className="chunk-reader-label">
                {t("chunkViewer.chunkLabel", { index: index + 1 })}
                {current.page != null && <> · {t("chunkViewer.pageLabel", { page: current.page })}</>}
                {comments.length > 0 && (
                  <> · {t("chunkViewer.commentsCount", { count: comments.length })}</>
                )}
              </div>
              <article
                ref={textRef}
                className={`chunk-modal-text${canWrite ? " selectable" : ""}`}
                onMouseUp={handleTextSelection}
                onKeyUp={handleTextSelection}
              >
                {renderCommentedText(
                  current.text || "",
                  comments,
                  activeCommentId,
                  t("chunkViewer.commentedPart"),
                )}
              </article>

              {canWrite && selectedText && (
                <div ref={composeRef} className="chunk-comment-compose">
                  <div className="chunk-comment-selection">
                    <span className="chunk-comment-label">{t("chunkViewer.selectionLabel")}</span>
                    <q>{sanitizeText(selectedText)}</q>
                  </div>
                  <textarea
                    ref={commentInputRef}
                    rows={3}
                    placeholder={t("chunkViewer.commentPlaceholder")}
                    value={commentDraft}
                    onChange={(e) => setCommentDraft(e.target.value)}
                    disabled={submitting}
                  />
                  {commentError && (
                    <p className="chunk-comment-error">{sanitizeText(commentError)}</p>
                  )}
                  <button
                    type="button"
                    className="chunk-comment-submit"
                    disabled={submitting || commentDraft.trim().length < 2}
                    onClick={() => void handleSubmitComment()}
                  >
                    {submitting ? (
                      <Loader2 size={16} className="spin" />
                    ) : (
                      <MessageSquarePlus size={16} />
                    )}
                    {t("chunkViewer.saveComment")}
                  </button>
                </div>
              )}

              {comments.length > 0 && (
                <div className="chunk-comments-list">
                  <h3>{t("chunkViewer.commentsHeading")}</h3>
                  {comments.map((c) => (
                    <div
                      key={c.comment_id}
                      className={`chunk-comment-item${activeCommentId === c.comment_id ? " active" : ""}`}
                      onMouseEnter={() => setActiveCommentId(c.comment_id)}
                      onMouseLeave={() => setActiveCommentId(null)}
                      onFocus={() => setActiveCommentId(c.comment_id)}
                      onBlur={() => setActiveCommentId(null)}
                      tabIndex={0}
                      role="button"
                    >
                      <blockquote>{sanitizeText(c.selected_text)}</blockquote>
                      <p>{sanitizeText(c.comment_text)}</p>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </section>

        <aside className="chunk-modal-list-panel" aria-label={t("chunkViewer.listHeading")}>
          <div className="chunk-list-header">{t("chunkViewer.listHeading")}</div>
          {loading ? (
            <div className="chunk-list-loading">{t("chunkViewer.listLoading")}</div>
          ) : (
            <ul className="chunk-list" ref={listRef}>
              {chunks.map((chunk, i) => (
                <li key={chunk.chunk_id}>
                  <button
                    type="button"
                    ref={(el) => {
                      itemRefs.current[i] = el;
                    }}
                    className={`chunk-list-item${i === index ? " active" : ""}`}
                    onClick={() => selectIndex(i)}
                  >
                    <span className="chunk-list-num">{i + 1}:</span>
                    <span className="chunk-list-preview">{chunkPreview(chunk.text || "")}</span>
                    <span className="chunk-list-meta">
                      {chunk.page != null && <span className="chunk-list-page">p.{chunk.page}</span>}
                      {(chunk.comments?.length ?? 0) > 0 && (
                        <span className="chunk-list-comments">
                          {t("chunkViewer.commentsShort", { count: chunk.comments!.length })}
                        </span>
                      )}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>
      </div>
    </Modal>
  );
}
