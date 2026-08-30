import { createBdd } from "playwright-bdd";

import { requireData } from "../src/clients";
import {
  GUARDRAILS_BANNED_PHRASE,
  GUARDRAILS_CLEAN_CHAT_MESSAGE,
  GUARDRAILS_CLEAN_COMMENT,
} from "../src/guardrails";
import { expect, test } from "../support/fixtures";

const { Given, When, Then } = createBdd(test);

type SseEvent = { event: string; data: Record<string, unknown> };

function serviceHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "text/event-stream",
    "Content-Type": "application/json",
  };
  const apiKey = process.env.API_KEY?.trim();
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  const tenantId = process.env.API_TENANT_ID?.trim();
  if (tenantId) {
    headers["X-Tenant-Id"] = tenantId;
  }
  return headers;
}

function parseSse(raw: string): SseEvent[] {
  const normalized = raw.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const events: SseEvent[] = [];
  for (const block of normalized.split("\n\n")) {
    if (!block.trim()) {
      continue;
    }
    let event = "message";
    let dataLine = "";
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) {
        event = line.slice("event:".length).trim();
      } else if (line.startsWith("data:")) {
        dataLine = line.slice("data:".length).trim();
      }
    }
    if (!dataLine) {
      continue;
    }
    try {
      events.push({ event, data: JSON.parse(dataLine) as Record<string, unknown> });
    } catch {
      events.push({ event, data: { raw: dataLine } });
    }
  }
  return events;
}

async function streamChatMessage(sessionId: string, message: string): Promise<SseEvent[]> {
  const base = process.env.CHAT_BASE_URL ?? "http://localhost:8002";
  const response = await fetch(`${base}/v1/chat/sessions/${sessionId}/stream`, {
    method: "POST",
    headers: serviceHeaders(),
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    throw new Error(`chat stream failed: HTTP ${response.status}`);
  }
  const raw = await response.text();
  return parseSse(raw);
}

Given("guardrails profile services are reachable", async () => {
  const base = process.env.GUARD_API_BASE ?? "http://localhost:8010";
  const token = process.env.GUARD_AUTH_TOKEN ?? "poc-local-classifier";
  const health = await fetch(`${base.replace(/\/$/, "")}/healthz`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!health.ok) {
    throw new Error(
      `llm-guard not reachable at ${base} (HTTP ${health.status}). Run: make up-guardrails`,
    );
  }
});

Given("an indexed chunk is available for comments", async ({ api, memory }) => {
  const fromEnv = process.env.API_TEST_CHUNK_ID?.trim();
  if (fromEnv) {
    memory.chunkId = fromEnv;
    return;
  }
  const docs = requireData(
    await api.GET("/v1/retrieval/indexed-documents"),
    "API GET /v1/retrieval/indexed-documents",
  );
  if (!docs.length) {
    throw new Error(
      "No indexed documents — upload+index a PDF or set API_TEST_CHUNK_ID for comment guardrails scenarios",
    );
  }
  const chunks = requireData(
    await api.GET("/v1/retrieval/documents/{doc_id}/chunks", {
      params: { path: { doc_id: docs[0].doc_id } },
    }),
    "API GET /v1/retrieval/documents/{doc_id}/chunks",
  );
  const chunkId = chunks.chunks[0]?.chunk_id;
  if (!chunkId) {
    throw new Error(`Document ${docs[0].doc_id} has no chunks`);
  }
  memory.chunkId = chunkId;
});

When("I stream a chat message containing the banned obscenity phrase", async ({ chat, memory }) => {
  const created = requireData(
    await chat.POST("/v1/chat/sessions", { body: { title: "api-guardrails-ban" } }),
    "chat POST /v1/chat/sessions",
  );
  memory.session = created;
  memory.sseEvents = await streamChatMessage(
    created.id,
    `Please summarize this: ${GUARDRAILS_BANNED_PHRASE}`,
  );
});

When("I stream a clean chat message for guardrails", async ({ chat, memory }) => {
  const created = requireData(
    await chat.POST("/v1/chat/sessions", { body: { title: "api-guardrails-clean" } }),
    "chat POST /v1/chat/sessions",
  );
  memory.session = created;
  memory.sseEvents = await streamChatMessage(created.id, GUARDRAILS_CLEAN_CHAT_MESSAGE);
});

Then("the chat stream should refuse with a guard block", async ({ memory }) => {
  const events = memory.sseEvents ?? [];
  const done = events.find((e) => e.event === "done");
  expect(done, "expected SSE done event").toBeTruthy();
  const answer = String(done?.data.answer ?? "");
  expect(answer.length).toBeGreaterThan(0);
  expect(answer.toLowerCase()).toMatch(/security check|rejected|injection|guard/);

  const rewrite = events.some((e) => e.event === "reasoning" && e.data.step === "rewrite");
  expect(rewrite, "blocked run must not continue to rewrite").toBe(false);
});

Then("the chat stream should pass the guard node", async ({ memory }) => {
  const events = memory.sseEvents ?? [];
  const done = events.find((e) => e.event === "done");
  expect(done, "expected SSE done event").toBeTruthy();
  const answer = String(done?.data.answer ?? "");
  expect(answer.length).toBeGreaterThan(0);
  expect(answer.toLowerCase()).not.toMatch(/prompt injection attempt|rejected by the security check/);

  const pastGuard = events.some(
    (e) =>
      e.event === "reasoning" &&
      (e.data.step === "rewrite" || e.data.step === "retrieve" || e.data.step === "generate"),
  );
  expect(pastGuard || answer.length > 0, "clean message should continue past guard").toBe(true);
});

When("I submit a chunk comment containing the banned obscenity phrase", async ({ api, memory }) => {
  expect(memory.chunkId).toBeTruthy();
  const result = await api.POST("/v1/annotations/chunks/{chunk_id}/comments", {
    params: { path: { chunk_id: memory.chunkId! } },
    body: {
      selected_text: "Relevant excerpt for annotation.",
      comment_text: `Note: ${GUARDRAILS_BANNED_PHRASE} in this clause.`,
    },
  });
  memory.commentStatus = result.response.status;
  memory.commentBody = result.error ?? result.data ?? null;
});

When("I submit a clean chunk comment for guardrails", async ({ api, memory }) => {
  expect(memory.chunkId).toBeTruthy();
  const result = await api.POST("/v1/annotations/chunks/{chunk_id}/comments", {
    params: { path: { chunk_id: memory.chunkId! } },
    body: {
      selected_text: "Relevant excerpt for annotation.",
      comment_text: GUARDRAILS_CLEAN_COMMENT,
    },
  });
  memory.commentStatus = result.response.status;
  memory.commentBody = result.error ?? result.data ?? null;
});

Then("the chunk comment should be rejected by the guard", async ({ memory }) => {
  expect(memory.commentStatus).toBe(422);
  const body = memory.commentBody as
    | { detail?: { rejection_reason?: string } | string }
    | null;
  const detail = body?.detail;
  const reason =
    typeof detail === "string"
      ? detail
      : detail && typeof detail === "object"
        ? detail.rejection_reason
        : undefined;
  expect(reason).toBeTruthy();
});

Then("the chunk comment should be accepted", async ({ memory }) => {
  expect(memory.commentStatus).toBe(200);
  const body = memory.commentBody as { comment_id?: string } | null;
  expect(body?.comment_id).toBeTruthy();
});
