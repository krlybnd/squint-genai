import { createBdd } from "playwright-bdd";

import { createApiClient } from "../src/clients";
import { fetchAccessToken } from "../src/keycloak";
import { expect, test } from "../support/fixtures";

const { When, Then } = createBdd(test);

const UNAUTH = { bearer: null, apiKey: null, tenantId: null } as const;

async function bearerApi(who: string) {
  const token = await fetchAccessToken(who);
  return createApiClient({ bearer: token, apiKey: null, tenantId: null });
}

When("I GET my profile as {string}", async ({ memory }, who: string) => {
  const result = await (await bearerApi(who)).GET("/v1/me");
  memory.httpStatus = result.response.status;
  memory.me = result.data;
});

When("I GET my profile without a bearer token", async ({ memory }) => {
  const result = await createApiClient(UNAUTH).GET("/v1/me");
  memory.httpStatus = result.response.status;
  memory.me = result.data;
});

When(
  "I set my active tenant to {string} as {string}",
  async ({ memory }, alias: string, who: string) => {
    const result = await (await bearerApi(who)).PUT("/v1/me/active-tenant", {
      body: { alias },
    });
    memory.httpStatus = result.response.status;
    memory.me = result.data;
  },
);

Then("my profile tenant_id should be {string}", async ({ memory }, tenantId: string) => {
  expect(memory.me).toBeDefined();
  expect(memory.me?.tenant_id).toBe(tenantId);
});

Then("my profile tenants should include {string}", async ({ memory }, alias: string) => {
  expect(memory.me).toBeDefined();
  expect(memory.me?.tenants?.some((tenant) => tenant.alias === alias)).toBe(true);
});
