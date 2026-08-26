import { buildHeadersAsync, chatBase } from "./http";
import type { ChatMessage, ChatSchemas, ChatSession } from "./types";

export async function fetchSessions(): Promise<ChatSession[]> {
  const res = await fetch(`${chatBase()}/v1/chat/sessions`, { headers: await buildHeadersAsync(false) });
  if (!res.ok) throw new Error("Failed to fetch sessions");
  return res.json();
}

export async function createSession(title?: string): Promise<ChatSession> {
  const body: ChatSchemas["CreateSessionRequest"] = { title: title ?? null };
  const res = await fetch(`${chatBase()}/v1/chat/sessions`, {
    method: "POST",
    headers: await buildHeadersAsync(),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Failed to create session (${res.status})`);
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${chatBase()}/v1/chat/sessions/${sessionId}`, {
    method: "DELETE",
    headers: await buildHeadersAsync(false),
  });
  if (!res.ok) throw new Error(`Failed to delete session (${res.status})`);
}

export async function fetchMessages(sessionId: string): Promise<ChatMessage[]> {
  const res = await fetch(`${chatBase()}/v1/chat/sessions/${sessionId}/messages`, {
    headers: await buildHeadersAsync(false),
  });
  if (!res.ok) throw new Error("Failed to fetch messages");
  return res.json();
}

export async function truncateMessagesFrom(
  sessionId: string,
  messageId: string,
): Promise<void> {
  const res = await fetch(
    `${chatBase()}/v1/chat/sessions/${sessionId}/messages/${messageId}/tail`,
    { method: "DELETE", headers: await buildHeadersAsync(false) },
  );
  if (!res.ok) throw new Error(`Failed to truncate messages (${res.status})`);
}
