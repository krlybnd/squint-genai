import { createBdd } from "playwright-bdd";
import { humanClick, humanFill, humanPress } from "../support/human";
import { expect, test } from "../support/fixtures";

const { When, Then } = createBdd(test);

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
  await expect(page.locator(".session-drawer-title").filter({ hasText: title }).first()).toBeVisible();
});

When("I wait until chat is not streaming", async ({ page }) => {
  await expect(page.locator(".btn-pause")).toHaveCount(0, { timeout: 90_000 });
  await expect(page.locator(".message-bubble.streaming")).toHaveCount(0, { timeout: 10_000 });
});

When("I wait until the active session can be deleted", async ({ page }) => {
  const deleteBtn = page.locator(".session-drawer-item.active .session-drawer-delete");
  await expect(deleteBtn).toBeEnabled({ timeout: 90_000 });
});

When("I delete the active session from the drawer", async ({ page }) => {
  await humanClick(page, page.locator(".session-drawer-item.active .session-drawer-delete"));
  await expect(page.locator(".session-drawer-item.active .session-drawer-delete .spin")).toHaveCount(0, {
    timeout: 30_000,
  });
});

When("I delete the session {string} from the drawer", async ({ page }, title: string) => {
  const item = page
    .locator(".session-drawer-item")
    .filter({ has: page.locator(".session-drawer-title", { hasText: title }) })
    .first();
  await humanClick(page, item.locator(".session-drawer-delete"));
  await expect(item).toHaveCount(0, { timeout: 30_000 });
});

When("I delete the current chat session from the drawer", async ({ page }) => {
  const title = (await page.locator(".chat-session-title").textContent())?.trim();
  if (!title) throw new Error("No active chat session title in toolbar");
  const matching = page.locator(".session-drawer-item").filter({
    has: page.locator(".session-drawer-title", { hasText: title }),
  });
  const before = await matching.count();
  await humanClick(page, matching.first().locator(".session-drawer-delete"));
  await expect(matching).toHaveCount(before - 1, { timeout: 30_000 });
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
  await expect(page.locator(".chat-session-title")).toHaveCount(0);
});

Then("the sessions list should show {string}", async ({ page }, text: string) => {
  await expect(page.locator(".session-drawer-empty")).toHaveText(text);
});
