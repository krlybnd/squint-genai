import { createBdd } from "playwright-bdd";

import { createApiClient } from "../src/clients";
import { fetchAccessToken } from "../src/keycloak";
import { expect, test } from "../support/fixtures";

const { Given, Then } = createBdd(test);

const UNAUTH = { bearer: null, apiKey: null, tenantId: null } as const;

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

Then("the HTTP status should be {int}", async ({ memory }, status: number) => {
  expect(memory.httpStatus).toBe(status);
});
