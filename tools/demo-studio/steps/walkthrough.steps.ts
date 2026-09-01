import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createBdd, defineParameterType } from "playwright-bdd";
import { test } from "../support/fixtures";
import { humanMoveTo, humanPause } from "../support/human";
import { ACTION_TIMEOUT_MS } from "../support/timeouts";
import { leaveCard } from "../support/card-fade";
import { walkthrough } from "../support/walkthrough";

defineParameterType({
  name: "holds",
  regexp: /\(\s*\d+(?:\s*,\s*\d+)*\s*\)/,
  transformer(raw: string): number[] {
    return raw
      .slice(1, -1)
      .split(",")
      .map((n) => Number(n.trim()));
  },
});

const { Given, When } = createBdd(test);
const cardsDir = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");

Given("I start a walkthrough recording", async ({ page }) => {
  await humanPause(page, 300);
});

async function openCard(page: import("@playwright/test").Page, file: string, marker: string) {
  await leaveCard(page);
  await page.goto(pathToFileURL(path.join(cardsDir, file)).href);
  await page.locator(marker).waitFor({ state: "visible", timeout: ACTION_TIMEOUT_MS });
}

When("I open the banner card", async ({ page }) => {
  await openCard(page, "banner-card.html", "[data-banner-card]");
});

When("I open the title card", async ({ page }) => {
  await openCard(page, "title-card.html", "[data-title-card]");
});

When("I open the summary", async ({ page }) => {
  await openCard(page, "summary.html", "[data-summary]");
});

When("I open the agenda", async ({ page }) => {
  await openCard(page, "agenda.html", "[data-agenda]");
});

When("the caption is {string} {holds}", async ({ page }, key: string, holds: number[]) => {
  await walkthrough.beginCaption(page, key, holds);
});

When("I wait {int} seconds", async ({ page }, seconds: number) => {
  await page.waitForTimeout(seconds * 1000);
});

When("I keep the pointer still", async ({ page }) => {
  await humanPause(page, 200);
});

When("I hover over the first anonymized phrase", async ({ page }) => {
  const mark = page.locator(".vault-reveal").first();
  await mark.waitFor({ state: "visible", timeout: 15_000 });
  await humanMoveTo(page, mark);
  await mark.hover();
});
