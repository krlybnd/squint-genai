import { createBdd } from "playwright-bdd";

import { createAdminClient, createApiClient, type ApiClient } from "../src/clients";
import { fetchAccessToken } from "../src/keycloak";
import { expect, test } from "../support/fixtures";

const { Given, When, Then } = createBdd(test);

const UNAUTH = { bearer: null, apiKey: null, tenantId: null } as const;

async function bearerApi(who: string, tenantId?: string | null): Promise<ApiClient> {
  const token = await fetchAccessToken(who);
  return createApiClient({ bearer: token, apiKey: null, tenantId: tenantId ?? null });
}

/** openapi-typescript `--path-params-as-types` collides `/v1/documents/{id}` with `/upload/presign`. */
function presignUpload(api: ApiClient, filename: string) {
  return (
    api as unknown as {
      POST: (
        url: "/v1/documents/upload/presign",
        init: { body: { filename: string } },
      ) => Promise<{ data?: { document?: { id: string } }; response: Response }>;
    }
  ).POST("/v1/documents/upload/presign", { body: { filename } });
}

Given("JWT authentication is enforced", async () => {
  try {
    await fetchAccessToken("admin");
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    test.skip(true, `Keycloak token endpoint not reachable — make up-auth (${reason})`);
  }
  const result = await createApiClient(UNAUTH).GET("/v1/documents");
  if (result.response.status !== 401) {
    test.skip(
      true,
      `expected 401 without bearer, got ${result.response.status} (AUTH_MODE is not jwt)`,
    );
  }
});

When("I GET {string} without a bearer token", async ({ memory }, path: string) => {
  if (path !== "/v1/documents") {
    throw new Error(`unsupported unauthenticated path: ${path}`);
  }
  const result = await createApiClient(UNAUTH).GET("/v1/documents");
  memory.httpStatus = result.response.status;
});

When("I presign an upload as {string}", async ({ memory }, who: string) => {
  const result = await presignUpload(await bearerApi(who), "auth-isolation.pdf");
  memory.httpStatus = result.response.status;
  if (result.data?.document?.id) {
    memory.documentId = result.data.document.id;
  }
});

When("I GET {string} on admin as {string}", async ({ memory }, path: string, who: string) => {
  if (path !== "/v1/tenants") {
    throw new Error(`unsupported admin path: ${path}`);
  }
  const token = await fetchAccessToken(who);
  const admin = createAdminClient({ bearer: token, apiKey: null, tenantId: null });
  const result = await admin.GET("/v1/tenants");
  memory.httpStatus = result.response.status;
});

Given("a document presigned as {string}", async ({ memory }, who: string) => {
  const result = await presignUpload(await bearerApi(who), "auth-isolation.pdf");
  const documentId = result.data?.document?.id;
  if (!result.response.ok || !documentId) {
    throw new Error(`presign as ${who} failed: HTTP ${result.response.status}`);
  }
  memory.documentId = documentId;
  memory.httpStatus = result.response.status;
});

When("I GET that document as {string}", async ({ memory }, who: string) => {
  const documentId = memory.documentId;
  if (!documentId) {
    throw new Error("no documentId in scenario memory");
  }
  const api = await bearerApi(who);
  const result = await api.GET(`/v1/documents/${documentId}`, {
    params: { path: { document_id: documentId } },
  });
  memory.httpStatus = result.response.status;
});

When(
  "I GET that document as {string} with header X-Tenant-Id {string}",
  async ({ memory }, who: string, tenantId: string) => {
    const documentId = memory.documentId;
    if (!documentId) {
      throw new Error("no documentId in scenario memory");
    }
    const api = await bearerApi(who, tenantId);
    const result = await api.GET(`/v1/documents/${documentId}`, {
      params: { path: { document_id: documentId } },
    });
    memory.httpStatus = result.response.status;
  },
);

Then("the HTTP status should be {int}", async ({ memory }, status: number) => {
  expect(memory.httpStatus).toBe(status);
});
