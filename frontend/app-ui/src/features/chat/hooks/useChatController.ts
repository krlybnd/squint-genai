import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  createSession,
  deleteSession,
  fetchMessages,
  fetchSessions,
  streamChat,
  streamReplay,
  truncateMessagesFrom,
  type ChatMessage,
  type ChatSession,
  type Citation,
  type ChunkPreview,
  type StreamEvent,
} from "../../../api/client";
import { useAuth } from "@are/ui-core";
import type { ChunkViewerTarget } from "../../../shared/types/chunks";
import {
  REASONING_DEFAULT_H,
  REASONING_HEADER_H,
  REASONING_INPUT_RESERVE,
  REASONING_MESSAGES_MIN,
  REASONING_MIN_H,
} from "../constants";
import type { ReasoningLine, ReasoningRun } from "../types";
import { isDefaultSessionTitle } from "../utils";

interface UseChatControllerOptions {
  session: ChatSession | null;
  onSessionCreated: (s: ChatSession | null) => void;
}

export function useChatController({ session, onSessionCreated }: UseChatControllerOptions) {
  const { t } = useTranslation();
  const newChatDefault = t("chat.newChatDefault");
  const auth = useAuth();
  const canWrite = auth.hasAnyRole("write", "admin");

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState("");
  const [status, setStatus] = useState("");
  const [reasoningBySession, setReasoningBySession] = useState<Record<string, ReasoningRun[]>>({});
  const [reasoningOpen, setReasoningOpen] = useState(true);
  const [reasoningHeight, setReasoningHeight] = useState(REASONING_DEFAULT_H);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [chunkViewer, setChunkViewer] = useState<ChunkViewerTarget | null>(null);
  const [sessionTitle, setSessionTitle] = useState<string | null>(null);
  const [streamingSessionId, setStreamingSessionId] = useState<string | null>(null);
  const [messageEdits, setMessageEdits] = useState<Record<string, string>>({});

  const bottomRef = useRef<HTMLDivElement>(null);
  const reasoningLogRef = useRef<HTMLUListElement>(null);
  const chatMainRef = useRef<HTMLDivElement>(null);
  const streamAbortRef = useRef<AbortController | null>(null);
  const activeRunIdRef = useRef<string | null>(null);
  const activeSessionRef = useRef<ChatSession | null>(null);
  const streamingSessionIdRef = useRef<string | null>(null);
  const lastSessionIdRef = useRef<string | null>(null);

  const displaySessionId = streamingSessionId ?? session?.id ?? null;
  const reasoningRuns = displaySessionId ? (reasoningBySession[displaySessionId] ?? []) : [];
  const panelBodyHeight = reasoningOpen ? reasoningHeight : REASONING_HEADER_H;

  useEffect(() => {
    activeSessionRef.current = session;
  }, [session]);

  const loadSessions = useCallback(async () => {
    try {
      setSessions(await fetchSessions());
    } catch {
      /* backend may be down */
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (!session) {
      if (streamingSessionIdRef.current) {
        return;
      }
      setMessages([]);
      setSessionTitle(null);
      setMessageEdits({});
      lastSessionIdRef.current = null;
      return;
    }

    const sessionId = session.id;
    const switched = lastSessionIdRef.current !== sessionId;
    lastSessionIdRef.current = sessionId;

    if (!isDefaultSessionTitle(session.title, newChatDefault)) {
      setSessionTitle(session.title);
    } else if (switched) {
      setSessionTitle(null);
    }

    if (!switched) {
      return;
    }

    setMessageEdits({});
    if (streamingSessionIdRef.current === sessionId) {
      return;
    }

    let cancelled = false;
    fetchMessages(sessionId)
      .then((loaded) => {
        if (!cancelled && lastSessionIdRef.current === sessionId) {
          setMessages(loaded);
        }
      })
      .catch(() => {
        if (!cancelled && lastSessionIdRef.current === sessionId) {
          setMessages([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [session, newChatDefault]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamText]);

  useEffect(() => {
    if (reasoningOpen && reasoningLogRef.current) {
      reasoningLogRef.current.scrollTop = reasoningLogRef.current.scrollHeight;
    }
  }, [reasoningRuns, reasoningOpen, streaming]);

  const appendReasoningRun = useCallback((sessionId: string, query: string) => {
    const runId = crypto.randomUUID();
    activeRunIdRef.current = runId;
    setReasoningBySession((prev) => ({
      ...prev,
      [sessionId]: [
        ...(prev[sessionId] ?? []),
        { id: runId, at: new Date().toISOString(), query, lines: [] },
      ],
    }));
    setReasoningOpen(true);
    return runId;
  }, []);

  const applyReasoning = useCallback(
    (event: Extract<StreamEvent, { type: "reasoning" }>) => {
      const runId = activeRunIdRef.current;
      const sessionId = streamingSessionIdRef.current ?? session?.id;
      if (!runId || !sessionId) return;

      setReasoningBySession((prev) => {
        const runs = prev[sessionId] ?? [];
        return {
          ...prev,
          [sessionId]: runs.map((run) => {
            if (run.id !== runId) return run;
            const entry: ReasoningLine = {
              step: event.step,
              message: event.message,
              status: event.status,
              chunks: event.chunks,
              piiRedactions: event.pii_redactions,
              piiDetails: event.pii_details,
              safeQuery: event.safe_query,
              checkpointId: event.checkpoint_id ?? undefined,
              needsRetrieval: event.needs_retrieval,
              searchQuery: event.search_query,
              rewriteReason: event.rewrite_reason,
              indexedDocumentCount: event.indexed_document_count,
              searchMeta: event.search_meta,
            };
            const idx = run.lines.findIndex((line) => line.step === event.step);
            const lines =
              idx >= 0
                ? run.lines.map((line, i) => (i === idx ? entry : line))
                : [...run.lines, entry];
            return { ...run, lines };
          }),
        };
      });
    },
    [session?.id],
  );

  const finishStream = useCallback(
    (cancelled = false) => {
      const runId = activeRunIdRef.current;
      const sessionId = streamingSessionIdRef.current ?? session?.id;
      if (cancelled && runId && sessionId) {
        setReasoningBySession((prev) => {
          const runs = prev[sessionId] ?? [];
          return {
            ...prev,
            [sessionId]: runs.map((run) => {
              if (run.id !== runId) return run;
              const withoutCancelled = run.lines.filter((l) => l.step !== "cancelled");
              return {
                ...run,
                lines: [
                  ...withoutCancelled.map((l) =>
                    l.status === "active" ? { ...l, status: "done" as const } : l,
                  ),
                  {
                    step: "cancelled",
                    message: t("chat.cancelled"),
                    status: "done" as const,
                  },
                ],
              };
            }),
          };
        });
      } else if (runId && sessionId) {
        setReasoningBySession((prev) => {
          const runs = prev[sessionId] ?? [];
          return {
            ...prev,
            [sessionId]: runs.map((run) => {
              if (run.id !== runId) return run;
              return {
                ...run,
                lines: run.lines.map((l) =>
                  l.status === "active" ? { ...l, status: "done" as const } : l,
                ),
              };
            }),
          };
        });
      }
      streamAbortRef.current = null;
      activeRunIdRef.current = null;
      streamingSessionIdRef.current = null;
      setStreamingSessionId(null);
      setStreaming(false);
      setStatus("");
      setStreamText("");
    },
    [session?.id, t],
  );

  const handleStreamEvent = useCallback(
    (event: StreamEvent) => {
      if (event.type === "reasoning") applyReasoning(event);
      if (event.type === "session") {
        setSessions((prev) =>
          prev.map((s) => (s.id === event.session_id ? { ...s, title: event.title } : s)),
        );
        setSessionTitle(event.title);
        const current = activeSessionRef.current;
        if (current?.id === event.session_id) {
          onSessionCreated({ ...current, title: event.title });
        }
      }
      if (event.type === "status") setStatus(event.step);
      if (event.type === "token") {
        setStreamText((prev) => prev + event.content);
      }
      if (event.type === "done") {
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === "assistant") {
            return prev.map((m, i) =>
              i === prev.length - 1
                ? {
                    ...m,
                    content: event.answer,
                    citations: event.citations,
                  }
                : m,
            );
          }
          return [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: event.answer,
              citations: event.citations,
              created_at: new Date().toISOString(),
            },
          ];
        });
        finishStream(false);
        loadSessions();
      }
      if (event.type === "cancelled") {
        finishStream(true);
      }
      if (event.type === "error") {
        setError(event.message || "Chat request failed.");
        finishStream(false);
      }
    },
    [applyReasoning, finishStream, loadSessions, onSessionCreated],
  );

  const getMessageText = useCallback(
    (message: ChatMessage) => messageEdits[message.id] ?? message.content,
    [messageEdits],
  );

  const truncateForReplay = useCallback(
    (sessionId: string, runId: string, fromStep?: string) => {
      setReasoningBySession((prev) => {
        const runs = prev[sessionId] ?? [];
        const runIndex = runs.findIndex((r) => r.id === runId);
        if (runIndex < 0) return prev;

        const keptRuns = runs.slice(0, runIndex + 1).map((run, idx) => {
          if (idx !== runIndex) return run;
          if (!fromStep) {
            return { ...run, lines: [] };
          }
          const lineIndex = run.lines.findIndex((l) => l.step === fromStep);
          if (lineIndex < 0) return { ...run, lines: [] };
          return {
            ...run,
            lines: run.lines.slice(0, lineIndex + 1).map((l) =>
              l.step === fromStep ? { ...l, status: "done" as const } : l,
            ),
          };
        });

        return { ...prev, [sessionId]: keptRuns };
      });
    },
    [],
  );

  const removeLastAssistantMessage = useCallback(() => {
    setMessages((prev) => {
      for (let i = prev.length - 1; i >= 0; i -= 1) {
        if (prev[i].role === "assistant") {
          return [...prev.slice(0, i), ...prev.slice(i + 1)];
        }
      }
      return prev;
    });
  }, []);

  const handleReplay = useCallback(
    (run: ReasoningRun, checkpointId?: string | null, fromStep?: string) => {
      if (!canWrite || streaming || !session?.id) return;
      setError("");
      truncateForReplay(session.id, run.id, fromStep);
      removeLastAssistantMessage();
      activeRunIdRef.current = run.id;
      setStreamingSessionId(session.id);
      streamingSessionIdRef.current = session.id;
      setStreaming(true);
      setStreamText("");
      setStatus("");
      streamAbortRef.current = streamReplay(
        session.id,
        {
          run_id: run.id,
          query: run.query,
          checkpoint_id: checkpointId ?? null,
        },
        handleStreamEvent,
      );
    },
    [
      canWrite,
      streaming,
      session?.id,
      truncateForReplay,
      removeLastAssistantMessage,
      handleStreamEvent,
    ],
  );

  const handleUserMessageResend = useCallback(
    async (message: ChatMessage, messageIndex: number) => {
      if (!canWrite || streaming || !session) return;
      const text = getMessageText(message).trim();
      if (!text) return;
      if (!window.confirm(t("chat.resendConfirm"))) return;

      setError("");
      const userTurnIndex =
        messages.slice(0, messageIndex + 1).filter((m) => m.role === "user").length - 1;
      const existingRun = (reasoningBySession[session.id] ?? [])[userTurnIndex];
      const runId = existingRun?.id ?? crypto.randomUUID();

      try {
        await truncateMessagesFrom(session.id, message.id);
      } catch {
        setError(t("chat.resendError"));
        return;
      }

      setMessages((prev) => prev.slice(0, messageIndex));
      setMessageEdits((prev) => {
        const next = { ...prev };
        delete next[message.id];
        return next;
      });
      setReasoningBySession((prev) => ({
        ...prev,
        [session.id]: [
          ...(prev[session.id] ?? []).slice(0, userTurnIndex),
          { id: runId, at: new Date().toISOString(), query: text, lines: [] },
        ],
      }));

      setStreaming(true);
      setStreamText("");
      setStatus("");
      setStreamingSessionId(session.id);
      streamingSessionIdRef.current = session.id;
      activeRunIdRef.current = runId;
      activeSessionRef.current = session;

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "user",
          content: text,
          citations: [],
          created_at: new Date().toISOString(),
        },
      ]);

      streamAbortRef.current = streamChat(session.id, text, handleStreamEvent, runId);
    },
    [
      canWrite,
      streaming,
      session,
      getMessageText,
      t,
      messages,
      reasoningBySession,
      handleStreamEvent,
    ],
  );

  const handleSend = useCallback(async () => {
    if (!canWrite || !input.trim() || streaming) return;
    setError("");

    let activeSession = session;
    try {
      if (!activeSession) {
        activeSession = await createSession();
        activeSessionRef.current = activeSession;
        streamingSessionIdRef.current = activeSession.id;
        setStreamingSessionId(activeSession.id);
        onSessionCreated(activeSession);
        setSessions((prev) => [activeSession!, ...prev]);
      }
    } catch (err) {
      const detail = err instanceof Error ? err.message : "Unknown error";
      setError(
        detail.includes("(401)") || detail.includes("(403)")
          ? t("chat.sessionAuthError")
          : `${t("chat.sessionCreateError")} (${detail}).`,
      );
      return;
    }

    const userMsg = input.trim();
    setInput("");
    setStreaming(true);
    setStreamText("");
    setStatus("");
    setStreamingSessionId(activeSession.id);
    streamingSessionIdRef.current = activeSession.id;
    const runId = appendReasoningRun(activeSession.id, userMsg);

    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: userMsg,
        citations: [],
        created_at: new Date().toISOString(),
      },
    ]);

    activeSessionRef.current = activeSession;
    streamAbortRef.current = streamChat(activeSession.id, userMsg, handleStreamEvent, runId);
  }, [
    canWrite,
    input,
    streaming,
    session,
    onSessionCreated,
    t,
    appendReasoningRun,
    handleStreamEvent,
  ]);

  const handleNewChat = useCallback(async () => {
    if (streaming) return;
    const s = await createSession();
    setSessions((prev) => [s, ...prev]);
    onSessionCreated(s);
    setDrawerOpen(false);
  }, [streaming, onSessionCreated]);

  const handleSelectSession = useCallback(
    (s: ChatSession) => {
      if (streaming) return;
      onSessionCreated(s);
      setDrawerOpen(false);
    },
    [streaming, onSessionCreated],
  );

  const handleDeleteSession = useCallback(
    async (s: ChatSession, e: React.MouseEvent) => {
      e.stopPropagation();
      if (!canWrite || deletingId) return;
      if (streaming) {
        setError(t("chat.sessionDeleteWhileStreaming"));
        return;
      }
      setDeletingId(s.id);
      setError("");
      try {
        await deleteSession(s.id);
        setSessions((prev) => prev.filter((item) => item.id !== s.id));
        setReasoningBySession((prev) => {
          const next = { ...prev };
          delete next[s.id];
          return next;
        });
        if (session?.id === s.id) {
          onSessionCreated(null);
          setMessages([]);
        }
      } catch {
        setError(t("chat.sessionDeleteError"));
      } finally {
        setDeletingId(null);
      }
    },
    [canWrite, deletingId, streaming, session?.id, onSessionCreated, t],
  );

  const handlePause = useCallback(() => {
    streamAbortRef.current?.abort();
  }, []);

  const openCitation = useCallback(
    (citation: Citation) => {
      const sourceFile = citation.source_file?.trim();
      if (!sourceFile || !citation.chunk_id) {
        setError(t("chat.chunkOpenError"));
        return;
      }
      setChunkViewer({
        docId: citation.doc_id?.trim(),
        sourceFile,
        chunkId: citation.chunk_id,
      });
    },
    [t],
  );

  const openReasoningChunk = useCallback((chunk: ChunkPreview) => {
    const sourceFile = chunk.source_file?.trim();
    if (!sourceFile || !chunk.chunk_id) return;
    setChunkViewer({
      sourceFile,
      chunkId: chunk.chunk_id,
    });
  }, []);

  const startReasoningResize = useCallback(
    (e: React.MouseEvent) => {
      if (!reasoningOpen) return;
      e.preventDefault();
      const startY = e.clientY;
      const startH = reasoningHeight;
      const mainHeight = chatMainRef.current?.clientHeight ?? 0;
      const maxH = Math.max(
        REASONING_MIN_H,
        mainHeight - REASONING_INPUT_RESERVE - REASONING_MESSAGES_MIN,
      );

      const onMove = (ev: MouseEvent) => {
        const next = startH - (ev.clientY - startY);
        setReasoningHeight(Math.min(maxH, Math.max(REASONING_MIN_H, next)));
      };
      const onUp = () => {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
      };
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    },
    [reasoningOpen, reasoningHeight],
  );

  return {
    t,
    canWrite,
    session,
    sessions,
    drawerOpen,
    setDrawerOpen,
    messages,
    input,
    setInput,
    streaming,
    streamText,
    status,
    reasoningRuns,
    reasoningOpen,
    setReasoningOpen,
    reasoningHeight,
    panelBodyHeight,
    error,
    deletingId,
    chunkViewer,
    setChunkViewer,
    sessionTitle,
    messageEdits,
    setMessageEdits,
    bottomRef,
    reasoningLogRef,
    chatMainRef,
    getMessageText,
    handleUserMessageResend,
    handleSend,
    handleNewChat,
    handleSelectSession,
    handleDeleteSession,
    handlePause,
    openCitation,
    openReasoningChunk,
    handleReplay,
    startReasoningResize,
  };
}

export type ChatController = ReturnType<typeof useChatController>;
