import { createBdd } from "playwright-bdd";

import { requireData } from "../src/clients";
import { expect, test } from "../support/fixtures";

const { When, Then } = createBdd(test);

When("I GET the AI system card", async ({ api, memory }) => {
  const result = await api.GET("/v1/ai/system-card");
  memory.systemCard = requireData(result, "API GET /v1/ai/system-card");
});

Then(
  "the system card should include name purpose risk tier and oversight",
  async ({ memory }) => {
    const card = memory.systemCard;
    expect(card).toBeDefined();
    expect(typeof card?.system_name).toBe("string");
    expect(card?.system_name?.length).toBeGreaterThan(0);
    expect(typeof card?.purpose).toBe("string");
    expect(typeof card?.risk_tier).toBe("string");
    expect(typeof card?.human_oversight).toBe("boolean");
    expect(typeof card?.model_id).toBe("string");
    expect(typeof card?.provider).toBe("string");
  },
);
