import type { Page } from "@playwright/test";

const VAULT_MARK_RE =
  /\[\[vault:(<[A-Z0-9_]+_[A-F0-9]{8}>)\]\]([\s\S]*?)\[\[\/vault\]\]/g;
const PLACEHOLDER_RE = /<[A-Z][A-Z0-9]*_[A-F0-9]{8}>/g;

export type SseTrace = {
  safeQuery: string;
  searchQuery: string;
  rewriteReason: string;
  piiRedactions: number;
  vaultMarks: string[];
  placeholders: string[];
  answer: string;
  reasoning: { step: string; message: string }[];
};

export const emptySseTrace = (): SseTrace => ({
  safeQuery: "",
  searchQuery: "",
  rewriteReason: "",
  piiRedactions: 0,
  vaultMarks: [],
  placeholders: [],
  answer: "",
  reasoning: [],
});

/** Tee chat SSE in the page — Playwright cannot read a stream the app already consumed. */
export const sseInitScript = `(() => {
  if (window.__demoStudioSseHook) return;
  window.__demoStudioSseHook = true;
  window.__demoStudioSseBody = "";
  const orig = window.fetch;
  window.fetch = async function (...args) {
    const res = await orig.apply(this, args);
    const ct = res.headers.get("content-type") || "";
    if (!ct.includes("event-stream") || !res.body) return res;
    const [tap, play] = res.body.tee();
    void (async () => {
      const reader = tap.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      try {
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
        }
        buf += decoder.decode();
        window.__demoStudioSseBody = buf;
      } catch (e) {}
    })();
    return new Response(play, {
      status: res.status,
      statusText: res.statusText,
      headers: res.headers,
    });
  };
})();`;

function collectMarks(text: string): { vaultMarks: string[]; placeholders: string[] } {
  const vaultMarks = [...text.matchAll(new RegExp(VAULT_MARK_RE, "g"))].map(
    (m) => `${m[1]} → ${m[2]}`,
  );
  const placeholders = [...new Set(text.match(PLACEHOLDER_RE) ?? [])];
  return { vaultMarks, placeholders };
}

export function parseSseBody(body: string): SseTrace {
  const trace = emptySseTrace();
  const frames = body.replace(/\r\n/g, "\n").split(/\n\n+/);
  let seen = "";
  for (const frame of frames) {
    let eventType = "message";
    let data = "";
    for (const line of frame.split("\n")) {
      if (line.startsWith("event:")) eventType = line.slice(6).trim();
      if (line.startsWith("data:")) data = line.slice(5).trim();
    }
    if (!data) continue;
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(data) as Record<string, unknown>;
    } catch {
      continue;
    }
    if (eventType === "reasoning") {
      const step = String(parsed.step ?? "");
      const message = String(parsed.message ?? "");
      trace.reasoning.push({ step, message });
      if (typeof parsed.safe_query === "string" && parsed.safe_query) {
        trace.safeQuery = parsed.safe_query;
      }
      if (typeof parsed.search_query === "string" && parsed.search_query) {
        trace.searchQuery = parsed.search_query;
      }
      if (typeof parsed.rewrite_reason === "string" && parsed.rewrite_reason) {
        trace.rewriteReason = parsed.rewrite_reason;
      }
      if (typeof parsed.pii_redactions === "number") {
        trace.piiRedactions = parsed.pii_redactions;
      }
      seen += `${message}\n${parsed.safe_query ?? ""}\n${parsed.search_query ?? ""}\n`;
      if (parsed.search_meta) seen += JSON.stringify(parsed.search_meta);
      if (Array.isArray(parsed.pii_details)) seen += JSON.stringify(parsed.pii_details);
    } else if (eventType === "token" && typeof parsed.content === "string") {
      seen += parsed.content;
    } else if (eventType === "done" && typeof parsed.answer === "string") {
      trace.answer = parsed.answer;
      seen += parsed.answer;
    }
  }
  const marks = collectMarks(seen);
  trace.vaultMarks = marks.vaultMarks;
  trace.placeholders = marks.placeholders;
  const outboundMarks = collectMarks(`${trace.safeQuery}\n${trace.searchQuery}`);
  trace.placeholders = [...new Set([...trace.placeholders, ...outboundMarks.placeholders])];
  return trace;
}

export function resetSseTap(): void {
  /* body lives on the page; cleared when the next stream finishes */
}

export async function lastSseTrace(page: Page): Promise<SseTrace> {
  let body = "";
  for (let i = 0; i < 15; i++) {
    body = await page.evaluate(() => {
      const w = window as unknown as { __demoStudioSseBody?: string };
      return w.__demoStudioSseBody ?? "";
    });
    if (body.includes("event:")) break;
    await page.waitForTimeout(200);
  }
  return parseSseBody(body);
}
