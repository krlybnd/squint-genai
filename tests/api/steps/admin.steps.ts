import { createBdd } from "playwright-bdd";

import { requireData } from "../src/clients";
import { expect, test } from "../support/fixtures";

const { When, Then } = createBdd(test);

When("I list tenants", async ({ admin, memory }) => {
  const result = await admin.GET("/v1/tenants");
  memory.tenants = requireData(result, "admin GET /v1/tenants");
});

Then("the tenant list should include items", async ({ memory }) => {
  expect(memory.tenants).toBeDefined();
  expect(Array.isArray(memory.tenants?.items)).toBe(true);
});

When("I list users", async ({ admin, memory }) => {
  const result = await admin.GET("/v1/users");
  memory.users = requireData(result, "admin GET /v1/users");
});

Then("the user list should include items", async ({ memory }) => {
  expect(memory.users).toBeDefined();
  expect(Array.isArray(memory.users?.items)).toBe(true);
});
