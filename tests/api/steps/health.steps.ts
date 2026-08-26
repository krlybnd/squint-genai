import { createBdd } from "playwright-bdd";

import { requireData } from "../src/clients";
import { expect, test } from "../support/fixtures";

const { When, Then } = createBdd(test);

When("I request API health", async ({ api, memory }) => {
  const result = await api.GET("/health");
  memory.healthStatus = requireData(result, "API GET /health").status;
});

When("I request chat health", async ({ chat, memory }) => {
  const result = await chat.GET("/health");
  memory.healthStatus = requireData(result, "chat GET /health").status;
});

When("I request admin health", async ({ admin, memory }) => {
  const result = await admin.GET("/health");
  memory.healthStatus = requireData(result, "admin GET /health").status;
});

Then("the health status should be {string}", async ({ memory }, status: string) => {
  expect(memory.healthStatus).toBe(status);
});
