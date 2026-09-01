import { createBdd } from "playwright-bdd";
import { humanClick, humanPause } from "../support/human";
import { expect, test } from "../support/fixtures";

const { Given, When, Then } = createBdd(test);

Then("I should see an assistant reply within {int} seconds", async ({ page }, seconds: number) => {
  await expect(page.locator(".message.assistant .message-bubble").first()).toBeVisible({
    timeout: seconds * 1000,
  });
});

When("I wait until generation has stopped", async ({ page }) => {
  await expect(page.locator(".btn-pause")).toHaveCount(0, { timeout: 90_000 });
  await expect(page.locator(".message-bubble.streaming")).toHaveCount(0, { timeout: 10_000 });
  await humanPause(page, 1000);
});

Given("the sessions list is empty", async ({ page }) => {
  await humanClick(page, page.getByRole("button", { name: "Open sessions", exact: true }));
  const drawer = page.locator(".session-drawer.open");
  await expect(drawer).toBeVisible();
  let items = drawer.locator(".session-drawer-item");
  while ((await items.count()) > 0) {
    const item = items.first();
    const deleteBtn = item.locator(".session-drawer-delete");
    if (await deleteBtn.isEnabled()) {
      await humanClick(page, deleteBtn);
      await expect(deleteBtn.locator(".spin")).toHaveCount(0, { timeout: 30_000 });
    }
    await humanPause(page, 300);
    items = drawer.locator(".session-drawer-item");
  }
  await expect(drawer.locator(".session-drawer-empty")).toBeVisible();
  await humanClick(page, page.getByRole("button", { name: "Close sessions", exact: true }));
});

When("I wait until the session title is not {string}", async ({ page }, defaultTitle: string) => {
  await expect(page.locator(".chat-session-title")).not.toHaveText(defaultTitle, { timeout: 90_000 });
});

Then("the sessions list should contain the current session", async ({ page }) => {
  const title = (await page.locator(".chat-session-title").textContent())?.trim();
  if (!title) throw new Error("No session title in the toolbar");
  await expect(page.locator(".session-drawer-title").filter({ hasText: title }).first()).toBeVisible({
    timeout: 15_000,
  });
});

When("I wait until the current session can be deleted", async ({ page }) => {
  await expect(page.locator(".btn-pause")).toHaveCount(0, { timeout: 90_000 });
  await expect(page.locator(".message-bubble.streaming")).toHaveCount(0, { timeout: 10_000 });
  await expect(page.locator(".message.assistant .message-bubble").last()).toBeVisible({
    timeout: 90_000,
  });
  await humanPause(page, 2500);
  await expect(page.locator(".session-drawer-item.active .session-drawer-delete")).toBeEnabled({
    timeout: 30_000,
  });
});

When("I delete the current session", async ({ page }) => {
  const active = page.locator(".session-drawer-item.active");
  await expect(active).toHaveCount(1);
  const title = (await active.locator(".session-drawer-title").textContent())?.trim();

  let deleted = false;
  for (let attempt = 0; attempt < 6; attempt++) {
    await expect(page.locator(".btn-pause")).toHaveCount(0);
    await expect(page.locator(".message-bubble.streaming")).toHaveCount(0);
    if (attempt > 0) {
      await humanPause(page, 2000);
    }
    const deleteBtn = active.locator(".session-drawer-delete");
    if (!(await deleteBtn.isEnabled())) continue;
    await humanClick(page, deleteBtn);
    await expect(deleteBtn.locator(".spin")).toHaveCount(0, { timeout: 30_000 });
    if ((await page.locator(".chat-error").count()) === 0) {
      deleted = true;
      break;
    }
  }
  if (!deleted) {
    const err = (await page.locator(".chat-error").textContent())?.trim();
    throw new Error(err ? `Session delete failed: ${err}` : "Session delete failed");
  }
  if (title) {
    await expect(page.locator(".session-drawer-title", { hasText: title })).toHaveCount(0, {
      timeout: 15_000,
    });
  }
});

Then("I should not see a chat error", async ({ page }) => {
  await expect(page.locator(".chat-error")).toHaveCount(0);
});

Then("the current session should not be in the sessions list", async ({ page }) => {
  await expect(page.locator(".session-drawer-item.active")).toHaveCount(0);
});

Then("the sessions drawer should be closed", async ({ page }) => {
  await expect(page.locator(".session-drawer")).not.toHaveClass(/open/);
});
