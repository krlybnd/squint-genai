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
  const card = docCard(page, name);
  await humanClick(page, card.locator(".btn-doc-actions"));
  await expect(card.locator(".doc-actions-menu")).toBeVisible();
});

When("I choose delete document", async ({ page }) => {
  await humanClick(page, page.getByRole("button", { name: /^delete$|törlés|löschen/i }));
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
  await expect(page.getByText(/read-only access|nur lesezugriff|csak olvasás/i)).toBeVisible();
});

Then("I should see document action {string}", async ({ page }, label: string) => {
  await expect(page.getByRole("button", { name: label })).toBeVisible();
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
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByText(name)).toBeVisible();
});

Then("the documents sidebar heading should be {string}", async ({ page }, heading: string) => {
  await expect(page.locator(".documents-panel .panel-header h2")).toContainText(heading);
});

Then("the upload action should show {string}", async ({ page }, label: string) => {
  await expect(page.getByRole("button", { name: label })).toBeVisible();
});
