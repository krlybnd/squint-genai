import path from "node:path";
import { fileURLToPath } from "node:url";
import { createBdd } from "playwright-bdd";
import { expect, test } from "../support/fixtures";
import { humanClick, humanGoto, humanPause } from "../support/human";

const { Given, When, Then } = createBdd(test);
const fixturesDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../resources/eval");

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
    await humanPause(page, 400);
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

Then("I should see document {string}", async ({ page }, name: string) => {
  await expect(page.locator(".doc-name", { hasText: name }).first()).toBeVisible({ timeout: 60_000 });
});

When(
  "I wait until document {string} shows {string} within {int} seconds",
  async ({ page }, name: string, status: string, seconds: number) => {
    await expect(docCard(page, name).locator(".doc-status")).toContainText(status, {
      timeout: seconds * 1000,
    });
  },
);

Then("document {string} shows {string}", async ({ page }, name: string, status: string) => {
  await expect(docCard(page, name).locator(".doc-status")).toContainText(status, { timeout: 15_000 });
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
  await expect(page.locator(".chunk-modal-text")).toBeVisible({ timeout: 30_000 });
});

Then("I should see a document dialog", async ({ page }) => {
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.locator(".chunk-modal-text")).toBeVisible({ timeout: 30_000 });
});

When("I click chunk {int} in the list", async ({ page }, n: number) => {
  const item = page.locator(".chunk-list-item").nth(n - 1);
  await humanClick(page, item);
  await expect(item).toHaveClass(/active/);
});

When("I select a passage in the chunk", async ({ page }) => {
  const text = page.locator(".chunk-modal-text");
  await expect(text).toBeVisible();
  const pts = await text.evaluate((el) => {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let node: Node | null;
    while ((node = walker.nextNode())) {
      const value = node.textContent ?? "";
      if (value.trim().length < 24) continue;
      const parent = node.parentElement;
      if (parent?.closest(".vault-reveal")) continue;
      const start = value.search(/\S/);
      const end = Math.min(value.length, start + 36);
      const range = document.createRange();
      range.setStart(node, start);
      range.setEnd(node, end);
      const rect = range.getClientRects()[0];
      if (!rect || rect.width < 48 || rect.height < 8) continue;
      return {
        x0: rect.left + 6,
        y: rect.top + rect.height / 2,
        x1: rect.left + Math.min(rect.width - 6, 360),
      };
    }
    return null;
  });
  if (!pts) throw new Error("no selectable passage in chunk text");
  await page.mouse.move(pts.x0, pts.y, { steps: 16 });
  await page.mouse.down();
  await page.mouse.move(pts.x1, pts.y, { steps: 28 });
  await page.mouse.up();
  await expect(page.locator(".chunk-comment-compose")).toBeVisible({ timeout: 12_000 });
});

Then("I should see a comment error", async ({ page }) => {
  await expect(page.locator(".chunk-comment-error")).toBeVisible({ timeout: 60_000 });
});
