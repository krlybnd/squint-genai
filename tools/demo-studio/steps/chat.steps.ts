import { createBdd } from "playwright-bdd";
import { expect, test } from "../support/fixtures";
import { humanClick, humanPause } from "../support/human";

const { When, Then } = createBdd(test);

Then("I should see an assistant reply within {int} seconds", async ({ page }, seconds: number) => {
  await expect(page.locator(".message.assistant .message-bubble").first()).toBeVisible({
    timeout: seconds * 1000,
  });
});

When("I wait until generation has stopped", async ({ page }) => {
  await expect(page.locator(".btn-pause")).toHaveCount(0, { timeout: 90_000 });
  await expect(page.locator(".message-bubble.streaming")).toHaveCount(0, { timeout: 10_000 });
  await humanPause(page, 800);
});

When("I click the first source", async ({ page }) => {
  const chip = page.locator(".citation-chip").first();
  await expect(chip).toBeVisible({ timeout: 15_000 });
  await humanClick(page, chip);
});
