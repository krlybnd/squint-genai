import { buildHeadersAsync, chatBase } from "./http";
import type { ChatSchemas, StreamEvent } from "./types";

export function parseSsePart(part: string, onEvent: (event: StreamEvent) => void): boolean {
  const normalized = part.replace(/\r\n/g, "\n").trim();
  if (!normalized) return false;

  let eventType = "message";
  let data = "";
  for (const line of normalized.split("\n")) {
    if (line.startsWith("event:")) eventType = line.slice(6).trim();
    if (line.startsWith("data:")) data = line.slice(5).trim();
  }
  if (!data) return false;

  try {
    const parsed = JSON.parse(data);
    if (eventType === "run") {
      onEvent({ type: "run", run_id: parsed.run_id, replay: parsed.replay });
    } else if (eventType === "token") {
      onEvent({ type: "token", content: parsed.content });
    } else if (eventType === "status") {
      onEvent({ type: "status", step: parsed.step, chunks: parsed.chunks });
    } else if (eventType === "reasoning") {
      onEvent({
        type: "reasoning",
        step: parsed.step,
        message: parsed.message,
        status: parsed.status,
        chunks: parsed.chunks,
        pii_redactions: parsed.pii_redactions,
        pii_details: parsed.pii_details,
        safe_query: parsed.safe_query,
        checkpoint_id: parsed.checkpoint_id,
        needs_retrieval: parsed.needs_retrieval,
        search_query: parsed.search_query,
        rewrite_reason: parsed.rewrite_reason,
        indexed_document_count: parsed.indexed_document_count,
        search_meta: parsed.search_meta,
      });
    } else if (eventType === "done") {
      onEvent({ type: "done", answer: parsed.answer, citations: parsed.citations });
      return true;
    } else if (eventType === "session") {
      onEvent({
        type: "session",
        session_id: parsed.session_id,
        title: parsed.title,
      });
    } else if (eventType === "error") {
      onEvent({ type: "error", message: parsed.message });
    }
  } catch {
    /* ignore parse errors */
  }
  return false;
}

async function consumeEventStream(
  response: Response,
  onEvent: (event: StreamEvent) => void,
  incompleteMessage: string,
): Promise<void> {
  if (!response.ok || !response.body) {
    onEvent({ type: "error", message: incompleteMessage });
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      parseSsePart(part, onEvent);
    }
  }
  parseSsePart(buffer, onEvent);
}

export function streamChat(
  sessionId: string,
  message: string,
  onEvent: (event: StreamEvent) => void,
  runId?: string,
): AbortController {
  const controller = new AbortController();
  const body: ChatSchemas["ChatStreamRequest"] & { run_id?: string } = {
    message,
    ...(runId ? { run_id: runId } : {}),
  };

  void (async () => {
    try {
      const headers = await buildHeadersAsync();
      const res = await fetch(`${chatBase()}/v1/chat/sessions/${sessionId}/stream`, {
        method: "POST",
        headers: { ...headers, Accept: "text/event-stream" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      let sawDone = false;
      const wrapped = (event: StreamEvent) => {
        if (event.type === "done") sawDone = true;
        onEvent(event);
      };
      await consumeEventStream(res, wrapped, "Stream failed");
      if (!sawDone && !controller.signal.aborted) {
        onEvent({ type: "error", message: "Stream ended before response completed." });
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") onEvent({ type: "cancelled" });
      else onEvent({ type: "error", message: String(err) });
    }
  })();

  return controller;
}

export function streamReplay(
  sessionId: string,
  body: { run_id: string; query: string; checkpoint_id?: string | null },
  onEvent: (event: StreamEvent) => void,
): AbortController {
  const controller = new AbortController();

  void (async () => {
    try {
      const headers = await buildHeadersAsync();
      const res = await fetch(`${chatBase()}/v1/chat/sessions/${sessionId}/replay`, {
        method: "POST",
        headers: { ...headers, Accept: "text/event-stream" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      let sawDone = false;
      const wrapped = (event: StreamEvent) => {
        if (event.type === "done") sawDone = true;
        onEvent(event);
      };
      await consumeEventStream(res, wrapped, "Replay failed");
      if (!sawDone && !controller.signal.aborted) {
        onEvent({ type: "error", message: "Replay ended before response completed." });
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") onEvent({ type: "cancelled" });
      else onEvent({ type: "error", message: String(err) });
    }
  })();

  return controller;
}
