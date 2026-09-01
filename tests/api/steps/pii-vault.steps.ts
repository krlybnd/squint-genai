import { createBdd } from "playwright-bdd";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { requireData } from "../src/clients";
import { optionalAdminAccessToken } from "../src/keycloak";
import {
  PII_VAULT_EMAIL,
  PII_VAULT_NAME,
  PII_VAULT_PDF,
  PII_VAULT_TOKEN_PATTERN,
} from "../src/pii-vault";
import { expect, test } from "../support/fixtures";

const { Given, When, Then } = createBdd(test);

const FIXTURES_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), "../fixtures");

async function apiHeaders(tenantId?: string): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
  };
  const bearer = await optionalAdminAccessToken();
  if (bearer) {
    headers.Authorization = `Bearer ${bearer}`;
  }
  const apiKey = process.env.API_KEY?.trim();
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  headers["X-Tenant-Id"] = tenantId ?? process.env.API_TENANT_ID?.trim() ?? "default";
  return headers;
}

async function pollJobCompleted(apiBase: string, jobId: string): Promise<void> {
  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline) {
    const response = await fetch(`${apiBase}/v1/admin/jobs/${jobId}`, {
      headers: await apiHeaders(),
    });
    if (!response.ok) {
      throw new Error(`job poll failed: HTTP ${response.status}`);
    }
    const body = (await response.json()) as { status?: string; error_message?: string | null };
    if (body.status === "completed") {
      return;
    }
    if (body.status === "failed") {
      throw new Error(`index job failed: ${body.error_message ?? "unknown"}`);
    }
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }
  throw new Error(`index job ${jobId} did not complete in time`);
}

Given("index-time PII tokenization prerequisites are met", async () => {
  const analyzerBase = process.env.ANALYZER_API_BASE ?? "http://localhost:5002";
  try {
    const health = await fetch(`${analyzerBase.replace(/\/$/, "")}/health`);
    if (!health.ok) {
      test.skip(true, `presidio-analyzer not reachable at ${analyzerBase}. Run: make up-guardrails`);
    }
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    test.skip(true, `presidio-analyzer not reachable at ${analyzerBase} (${reason}). Run: make up-guardrails`);
  }
  if (process.env.PII_VAULT_TESTS_ENABLED !== "true") {
    test.skip(
      true,
      "Set PII_VAULT_TESTS_ENABLED=true, PII_VAULT_ENABLED=true, and INDEXING_PDF_PII_TOKENIZATION_ENABLED=true on indexing worker",
    );
  }
});

Given("a PDF with known PII is uploaded and indexed", async ({ api, memory }) => {
  const presign = requireData(
    await api.POST("/v1/documents/upload/presign", {
      body: { filename: PII_VAULT_PDF },
    }),
    "API POST /v1/documents/upload/presign",
  );
  const documentId = presign.document.id;
  const pdfBytes = readFileSync(path.join(FIXTURES_DIR, PII_VAULT_PDF));

  const uploadBase = process.env.API_BASE_URL ?? "http://localhost:8000";
  const upload = await fetch(`${uploadBase}/v1/documents/${documentId}/upload`, {
    method: "PUT",
    headers: {
      ...(await apiHeaders()),
      "Content-Type": "application/pdf",
    },
    body: pdfBytes,
  });
  if (!upload.ok) {
    throw new Error(`document upload failed: HTTP ${upload.status}`);
  }

  const complete = requireData(
    await api.POST("/v1/documents/{document_id}/complete", {
      params: { path: { document_id: documentId } },
    }),
    "API POST /v1/documents/{document_id}/complete",
  );
  await pollJobCompleted(uploadBase, complete.job_id);
  memory.piiDocId = documentId;
});

When("I search retrieval for the known PII name", async ({ api, memory }) => {
  const search = requireData(
    await api.POST("/v1/retrieval/search", {
      body: { query: PII_VAULT_NAME, top_k: 5 },
    }),
    "API POST /v1/retrieval/search",
  );
  memory.piiSearchChunks = search.chunks;
});

Then("the retrieval chunk text should not contain the plaintext PII", async ({ memory }) => {
  const chunks = memory.piiSearchChunks ?? [];
  expect(chunks.length).toBeGreaterThan(0);
  const combined = chunks.map((chunk) => chunk.text).join("\n");
  expect(combined).not.toContain(PII_VAULT_NAME);
  expect(combined).not.toContain(PII_VAULT_EMAIL);
});

Then("the retrieval chunk text should contain a vault token", async ({ memory }) => {
  const chunks = memory.piiSearchChunks ?? [];
  const combined = chunks.map((chunk) => chunk.text).join("\n");
  expect(combined).toMatch(PII_VAULT_TOKEN_PATTERN);
  const match = combined.match(PII_VAULT_TOKEN_PATTERN);
  memory.piiVaultToken = match?.[0];
});

Given("a vault token from indexed PII content", async ({ api, memory }) => {
  if (memory.piiVaultToken) {
    return;
  }
  const search = requireData(
    await api.POST("/v1/retrieval/search", {
      body: { query: "contract", top_k: 5 },
    }),
    "API POST /v1/retrieval/search",
  );
  const combined = search.chunks.map((chunk) => chunk.text).join("\n");
  const match = combined.match(PII_VAULT_TOKEN_PATTERN);
  if (!match) {
    throw new Error("no vault token found — run indexed PII upload scenario first or reindex");
  }
  memory.piiVaultToken = match[0];
});

When("I detokenize the vault token", async ({ memory }) => {
  const base = process.env.API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${base}/v1/vault/detokenize`, {
    method: "POST",
    headers: await apiHeaders(),
    body: JSON.stringify({ tokens: [memory.piiVaultToken] }),
  });
  memory.piiDetokenizeStatus = response.status;
  memory.piiDetokenizeBody = await response.json();
});

When("I detokenize the vault token as tenant B", async ({ memory }) => {
  const base = process.env.API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${base}/v1/vault/detokenize`, {
    method: "POST",
    headers: await apiHeaders("tenant-b"),
    body: JSON.stringify({ tokens: [memory.piiVaultToken] }),
  });
  memory.piiDetokenizeStatus = response.status;
  memory.piiDetokenizeBody = await response.json();
});

Then("the detokenize response should contain the plaintext PII", async ({ memory }) => {
  expect(memory.piiDetokenizeStatus).toBe(200);
  const body = memory.piiDetokenizeBody as { values?: Record<string, string> } | null;
  const token = memory.piiVaultToken;
  expect(token).toBeTruthy();
  const value = body?.values?.[token!];
  expect(value === PII_VAULT_NAME || value === PII_VAULT_EMAIL).toBe(true);
});

Then("the detokenize response should be empty", async ({ memory }) => {
  expect(memory.piiDetokenizeStatus).toBe(200);
  const body = memory.piiDetokenizeBody as { values?: Record<string, string> } | null;
  expect(Object.keys(body?.values ?? {}).length).toBe(0);
});
