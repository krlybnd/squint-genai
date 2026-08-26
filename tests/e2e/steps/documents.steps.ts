import path from "node:path";
import { fileURLToPath } from "node:url";
import { createBdd } from "playwright-bdd";
import { humanClick, humanGoto, humanPause } from "../support/human";
import { expect, test } from "../support/fixtures";

const { Given, When, Then } = createBdd(test);
const fixturesDir = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "fixtures");

function docCard(page: import("@playwright/test").Page, name: string) {
  return page.locator(".doc-card").filter({ has: page.locator(".doc-name", { hasText: name }) }).first();
}

async function openDocActionsMenu(page: import("@playwright/test").Page, name: string): Promise<void> {
  const card = docCard(page, name);
  await expect(card).toBeVisible();
  const actionsBtn = card.locator(".btn-doc-actions");
  await expect(actionsBtn.locator(".spin")).toHaveCount(0, { timeout: 60_000 });
  for (let attempt = 0; attempt < 3; attempt++) {
    await humanClick(page, actionsBtn);
    const menu = page.locator(".doc-actions-menu");
    if (await menu.isVisible()) return;
    await humanPause(page, 300);
  }
  await expect(page.locator(".doc-actions-menu")).toBeVisible({ timeout: 15_000 });
}

Given("the documents sidebar is empty", async ({ page }) => {
  await humanGoto(page, "/");
  await expect(page.locator(".documents-panel")).toBeVisible();
  await page.locator(".doc-list .doc-empty .spin").waitFor({ state: "detached", timeout: 30_000 }).catch(() => {});

  let cards = page.locator(".doc-card");
  while ((await cards.count()) > 0) {
    const before = await cards.count();
    const card = cards.first();
    const actionsBtn = card.locator(".btn-doc-actions");
    await expect(actionsBtn.locator(".spin")).toHaveCount(0, { timeout: 60_000 });
    await humanClick(page, actionsBtn);
    await expect(page.locator(".doc-actions-menu")).toBeVisible({ timeout: 10_000 });
    await humanClick(page, page.locator(".doc-actions-menu").getByRole("button", { name: /^delete$|törlés|löschen/i }));
    await expect(actionsBtn.locator(".spin")).toHaveCount(0, { timeout: 60_000 });
    await expect(cards).toHaveCount(before - 1, { timeout: 60_000 });
    await humanPause(page, 500);
    cards = page.locator(".doc-card");
  }
  await expect(page.locator(".doc-empty")).toBeVisible({ timeout: 30_000 });
});

Given("the documents list is loaded", async ({ page }) => {
  await humanGoto(page, "/");
  await expect(page.locator(".documents-panel .panel-header h2")).toBeVisible();
});

Given("the stack indexing worker is running", async () => {
  test.info().annotations.push({
    type: "note",
    description: "Requires docker compose stack with indexing worker healthy",
  });
});

When("I upload the fixture file {string} from the documents panel", async ({ page }, filename: string) => {
  const filePath = path.join(fixturesDir, filename);
  await humanClick(page, page.locator(".btn-upload"));
  await humanPause(page);
  await page.locator('input[type="file"]').setInputFiles(filePath);
  await humanPause(page, 800);
});

Then("a document card named {string} should appear in the sidebar", async ({ page }, name: string) => {
  await expect(page.locator(".doc-name", { hasText: name })).toBeVisible({ timeout: 60_000 });
});

Given('a document {string} exists in the sidebar', async ({ page }, name: string) => {
  await humanGoto(page, "/");
  const card = page.locator(".doc-name", { hasText: name });
  if (await card.isVisible()) return;
  const filePath = path.join(fixturesDir, name);
  await humanClick(page, page.locator(".btn-upload"));
  await humanPause(page);
  await page.locator('input[type="file"]').setInputFiles(filePath);
  await expect(card).toBeVisible({ timeout: 60_000 });
});

When("I open actions for document {string}", async ({ page }, name: string) => {
  await openDocActionsMenu(page, name);
});

When("I choose delete document", async ({ page }) => {
  await humanClick(page, page.locator(".doc-actions-menu").getByRole("button", { name: /^delete$|törlés|löschen/i }));
});

Then("document {string} should not appear in the sidebar", async ({ page }, name: string) => {
  await expect(page.locator(".doc-name", { hasText: name })).toHaveCount(0);
});

Then("the empty documents hint should be visible", async ({ page }) => {
  await expect(page.locator(".doc-empty")).toBeVisible();
});

Then("the upload PDF control should not be visible", async ({ page }) => {
  await expect(page.getByRole("button", { name: /upload pdf|pdf feltöltés/i })).toHaveCount(0);
});

Then("the read-only empty hint should be visible", async ({ page }) => {
  await expect(page.locator(".doc-empty")).toBeVisible();
  await expect(page.locator(".doc-empty")).toContainText(/read-only access|nur lesezugriff|csak olvas/i);
});

Then("I should see document action {string}", async ({ page }, label: string) => {
  await expect(page.locator(".doc-actions-menu").getByRole("button", { name: label })).toBeVisible();
});

Then('document {string} should show status {string} or {string}', async ({ page }, name, a, b) => {
  await expect(docCard(page, name).locator(".doc-status")).toContainText(new RegExp(`${a}|${b}`, "i"));
});

When(
  'I wait until document {string} shows status {string} within {int} seconds',
  async ({ page }, name, status, seconds) => {
    await expect(docCard(page, name).locator(".doc-status")).toContainText(status, {
      timeout: seconds * 1000,
    });
  },
);

Given('document {string} shows status {string}', async ({ page }, name, status) => {
  await humanGoto(page, "/");
  await expect(docCard(page, name).locator(".doc-status")).toContainText(status, { timeout: 120_000 });
});

Then('document {string} should show status {string}', async ({ page }, name, status) => {
  await expect(docCard(page, name).locator(".doc-status")).toContainText(status);
});

Then("the document card {string} should be clickable", async ({ page }, name: string) => {
  const card = page
    .locator(".doc-card.doc-card-clickable")
    .filter({ has: page.locator(".doc-name", { hasText: name }) })
    .first();
  await expect(card).toBeVisible();
});

When("I open document {string} from the sidebar", async ({ page }, name: string) => {
  const card = page
    .locator(".doc-card.doc-card-clickable")
    .filter({ has: page.locator(".doc-name", { hasText: name }) })
    .first();
  await humanClick(page, card);
});

Then("the chunk viewer modal should be visible for {string}", async ({ page }, name: string) => {
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("heading", { name })).toBeVisible();
});

Then("the documents sidebar heading should be {string}", async ({ page }, heading: string) => {
  await expect(page.locator(".documents-panel .panel-header h2")).toContainText(heading);
});

Then("the upload action should show {string}", async ({ page }, label: string) => {
  await expect(page.getByRole("button", { name: label })).toBeVisible();
});
