import { createBdd } from "playwright-bdd";

import { requireData } from "../src/clients";
import { expect, test } from "../support/fixtures";

const { When, Then } = createBdd(test);

When("I create a chat session titled {string}", async ({ chat, memory }, title: string) => {
  const result = await chat.POST("/v1/chat/sessions", { body: { title } });
  memory.session = requireData(result, "chat POST /v1/chat/sessions");
});

Then("the session should have an id", async ({ memory }) => {
  expect(memory.session?.id).toBeTruthy();
});

When("I list chat sessions", async ({ chat, memory }) => {
  const result = await chat.GET("/v1/chat/sessions");
  memory.sessions = requireData(result, "chat GET /v1/chat/sessions");
});

Then("the session list should include that session", async ({ memory }) => {
  const sessionId = memory.session?.id;
  expect(sessionId).toBeTruthy();
  expect(memory.sessions?.some((session) => session.id === sessionId)).toBe(true);
});
