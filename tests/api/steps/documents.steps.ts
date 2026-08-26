import { createBdd } from "playwright-bdd";

import { requireData } from "../src/clients";
import { expect, test } from "../support/fixtures";

const { When, Then } = createBdd(test);

When("I list documents", async ({ api, memory }) => {
  const result = await api.GET("/v1/documents");
  memory.documents = requireData(result, "API GET /v1/documents");
});

Then("the document list should include items and a total", async ({ memory }) => {
  expect(memory.documents).toBeDefined();
  expect(Array.isArray(memory.documents?.items)).toBe(true);
  expect(typeof memory.documents?.total).toBe("number");
});
