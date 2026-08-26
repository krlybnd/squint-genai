import { createBdd } from "playwright-bdd";
import { humanClick, humanFill, humanPause, humanPress } from "../support/human";
import { expect, test } from "../support/fixtures";

const { Given, When, Then } = createBdd(test);

When("I start a new chat from the toolbar", async ({ page }) => {
  await humanClick(page, page.locator(".btn-new-chat"));
});

Then("the chat empty title should be visible", async ({ page }) => {
  await expect(page.getByText(/ask anything about your documents/i)).toBeVisible();
});

Then("the chat input placeholder should be {string}", async ({ page }, placeholder: string) => {
  await expect(page.getByPlaceholder(placeholder)).toBeVisible();
});

When("I send the chat message {string}", async ({ page }, message: string) => {
  const input = page.getByPlaceholder(/ask a question|kérdés|frage/i);
  await humanFill(page, input, message);
  await humanPress(page, input, "Enter");
});

Then("I should see my message {string} in the thread", async ({ page }, message: string) => {
  await expect(page.getByText(message, { exact: true })).toBeVisible();
});

Then("I should receive an assistant reply within {int} seconds", async ({ page }, seconds: number) => {
  await expect(page.locator(".message.assistant .message-bubble").first()).toBeVisible({
    timeout: seconds * 1000,
  });
});

When("I open the sessions drawer", async ({ page }) => {
  await humanClick(page, page.getByRole("button", { name: /open sessions|sessions/i }));
});

When("I close the sessions drawer", async ({ page }) => {
  await humanClick(page, page.getByRole("button", { name: /close sessions|sessions/i }));
});

Then("the sessions panel title should be {string}", async ({ page }, title: string) => {
  await expect(page.locator(".session-drawer-header h3")).toHaveText(title);
});

Then("the sessions panel should be hidden", async ({ page }) => {
  await expect(page.locator(".session-drawer")).not.toHaveClass(/open/);
});

Then("the sessions list should contain a session with title matching {string}", async ({ page }, title: string) => {
  await expect(page.locator(".session-drawer-title").filter({ hasText: title }).first()).toBeVisible({
    timeout: 60_000,
  });
});

When("I wait until chat is not streaming", async ({ page }) => {
  await expect(page.locator(".btn-pause")).toHaveCount(0, { timeout: 90_000 });
  await expect(page.locator(".message-bubble.streaming")).toHaveCount(0, { timeout: 10_000 });
  await humanPause(page, 1000);
});

Given("the chat sessions list is empty", async ({ page }) => {
  await humanClick(page, page.getByRole("button", { name: /open sessions|sessions/i }));
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
  await humanClick(page, page.getByRole("button", { name: /close sessions|sessions/i }));
});

When("I wait until the session title is updated from default", async ({ page }) => {
  await expect(page.locator(".chat-session-title")).not.toHaveText(/^(New chat|Új beszélgetés|Neuer Chat)$/i, {
    timeout: 90_000,
  });
});

Then("the sessions list should contain the active session title", async ({ page }) => {
  const title = (await page.locator(".chat-session-title").textContent())?.trim();
  if (!title) throw new Error("No active session title in toolbar");
  await expect(page.locator(".session-drawer-title").filter({ hasText: title }).first()).toBeVisible({
    timeout: 15_000,
  });
});

When("I wait until the active session can be deleted", async ({ page }) => {
  await expect(page.locator(".btn-pause")).toHaveCount(0, { timeout: 90_000 });
  await expect(page.locator(".message-bubble.streaming")).toHaveCount(0, { timeout: 10_000 });
  await expect(page.locator(".message.assistant .message-bubble").last()).toBeVisible({
    timeout: 90_000,
  });
  await humanPause(page, 2500);
  const deleteBtn = page.locator(".session-drawer-item.active .session-drawer-delete");
  await expect(deleteBtn).toBeEnabled({ timeout: 30_000 });
});

When("I delete the current chat session from the drawer", async ({ page }) => {
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

Then("no chat error should be visible", async ({ page }) => {
  await expect(page.locator(".chat-error")).toHaveCount(0);
});

Then("the active session should be removed from the sessions list", async ({ page }) => {
  await expect(page.locator(".session-drawer-item.active")).toHaveCount(0);
});

Then("the session {string} should not appear in the sessions list", async ({ page }, title: string) => {
  await expect(page.locator(".session-drawer-title").filter({ hasText: title })).toHaveCount(0);
});

Then("the current chat session should not appear in the sessions list", async ({ page }) => {
  await expect(page.locator(".session-drawer-item.active")).toHaveCount(0);
});

Then("the sessions list should show {string}", async ({ page }, text: string) => {
  await expect(page.locator(".session-drawer-empty")).toHaveText(text);
});
