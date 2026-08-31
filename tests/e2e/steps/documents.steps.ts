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

async function waitForDocumentsLoaded(page: import("@playwright/test").Page) {
  await expect(page.locator(".documents-panel")).toBeVisible();
  await page.locator(".doc-list .doc-empty .spin").waitFor({ state: "detached", timeout: 30_000 }).catch(() => {});
}

Given("the documents list is empty", async ({ page }) => {
  await humanGoto(page, "/");
  await waitForDocumentsLoaded(page);

  let cards = page.locator(".doc-card");
  while ((await cards.count()) > 0) {
    const before = await cards.count();
    const card = cards.first();
    const actionsBtn = card.locator(".btn-doc-actions");
    await expect(actionsBtn.locator(".spin")).toHaveCount(0, { timeout: 60_000 });
    await humanClick(page, actionsBtn);
    await expect(page.locator(".doc-actions-menu")).toBeVisible({ timeout: 10_000 });
    await humanClick(page, page.getByRole("button", { name: "Delete", exact: true }));
    await expect(actionsBtn.locator(".spin")).toHaveCount(0, { timeout: 60_000 });
    await expect(cards).toHaveCount(before - 1, { timeout: 60_000 });
    await humanPause(page, 500);
    cards = page.locator(".doc-card");
  }
  await expect(page.locator(".doc-empty")).toBeVisible({ timeout: 30_000 });
});

When("I upload {string}", async ({ page }, filename: string) => {
  const filePath = path.join(fixturesDir, filename);
  await humanClick(page, page.getByRole("button", { name: "Upload PDF", exact: true }));
  await humanPause(page);
  await page.locator('input[type="file"]').setInputFiles(filePath);
  await humanPause(page, 800);
});

Given("the document {string} is in the sidebar", async ({ page }, name: string) => {
  await humanGoto(page, "/");
  await waitForDocumentsLoaded(page);
  const card = page.locator(".doc-name", { hasText: name });
  if ((await card.count()) > 0) return;
  const filePath = path.join(fixturesDir, name);
  await humanClick(page, page.getByRole("button", { name: "Upload PDF", exact: true }));
  await humanPause(page);
  await page.locator('input[type="file"]').setInputFiles(filePath);
  await expect(card).toBeVisible({ timeout: 60_000 });
});

When("I open {string} on document {string}", async ({ page }, actionTitle: string, name: string) => {
  const card = docCard(page, name);
  await expect(card).toBeVisible();
  const actionsBtn = card.getByRole("button", { name: actionTitle });
  await expect(actionsBtn.locator(".spin")).toHaveCount(0, { timeout: 60_000 });
  for (let attempt = 0; attempt < 3; attempt++) {
    await humanClick(page, actionsBtn);
    if (await page.locator(".doc-actions-menu").isVisible()) return;
    await humanPause(page, 300);
  }
  await expect(page.locator(".doc-actions-menu")).toBeVisible({ timeout: 15_000 });
});

Then("I should see document {string}", async ({ page }, name: string) => {
  await expect(page.locator(".doc-name", { hasText: name }).first()).toBeVisible({ timeout: 60_000 });
});

Then("I should not see document {string}", async ({ page }, name: string) => {
  await expect(page.locator(".doc-name", { hasText: name })).toHaveCount(0);
});

Then("I should see document action {string}", async ({ page }, label: string) => {
  await expect(page.locator(".doc-actions-menu").getByRole("button", { name: label, exact: true })).toBeVisible();
});

Then(
  "document {string} should show {string} or {string}",
  async ({ page }, name: string, a: string, b: string) => {
    await expect(docCard(page, name).locator(".doc-status")).toContainText(new RegExp(`${a}|${b}`, "i"));
  },
);

When(
  "I wait until document {string} shows {string} within {int} seconds",
  async ({ page }, name: string, status: string, seconds: number) => {
    await expect(docCard(page, name).locator(".doc-status")).toContainText(status, {
      timeout: seconds * 1000,
    });
  },
);

Given("document {string} shows {string}", async ({ page }, name: string, status: string) => {
  test.info().setTimeout(240_000);
  await humanGoto(page, "/");
  await waitForDocumentsLoaded(page);
  const card = page
    .locator(".doc-card")
    .filter({ has: page.locator(".doc-name", { hasText: name }) })
    .filter({ has: page.locator(".doc-status", { hasText: status }) });
  await expect(card.first()).toBeVisible({ timeout: 120_000 });
});

When("I open document {string}", async ({ page }, name: string) => {
  const card = page
    .locator(".doc-card.doc-card-clickable")
    .filter({ has: page.locator(".doc-name", { hasText: name }) })
    .first();
  await humanClick(page, card);
});

Then("I should see a dialog titled {string}", async ({ page }, name: string) => {
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("heading", { name, exact: true })).toBeVisible();
});
