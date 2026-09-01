import { createBdd } from "playwright-bdd";
import { humanClick, humanFill, humanGoto, humanPause, humanPress } from "../support/human";
import { credentialsForUser, loginViaKeycloak } from "../support/keycloak-login";
import { scenarioState } from "../support/scenario-state";
import { expect, test } from "../support/fixtures";

const { Given, When, Then } = createBdd(test);

When("I go to {string}", async ({ page }, path: string) => {
  await humanGoto(page, path === "/admin" ? "/admin/" : path);
});

When("I reload the page", async ({ page }) => {
  await page.reload();
  await humanPause(page);
  if (process.env.E2E_AUTH !== "0") {
    await page.locator(".profile-menu-name").waitFor({ timeout: 30_000 }).catch(() => {});
  }
});

When("I click the button {string}", async ({ page }, name: string) => {
  const profile = page.locator(".profile-menu-trigger").filter({
    has: page.locator(".profile-menu-name", { hasText: new RegExp(`^${name}$`, "i") }),
  });
  if ((await profile.count()) > 0) {
    await humanClick(page, profile);
    return;
  }
  await humanClick(page, page.getByRole("button", { name, exact: true }).first());
});

When("I click the menu item {string}", async ({ page }, name: string) => {
  await humanClick(page, page.getByRole("menuitem", { name, exact: true }));
});

When("I choose {string}", async ({ page }, name: string) => {
  await humanClick(page, page.getByRole("menuitemradio", { name, exact: true }));
});

When("I choose {string} from {string}", async ({ page }, option: string, trigger: string) => {
  const triggerBtn = page.getByRole("button", { name: trigger, exact: true });
  await humanClick(page, triggerBtn);
  await humanClick(page, page.getByRole("option", { name: option, exact: true }));
  await expect(triggerBtn).toContainText(option, { timeout: 30_000 });
});

When("I fill {string} with {string}", async ({ page }, label: string, value: string) => {
  const field = page.getByLabel(label, { exact: true }).or(page.getByPlaceholder(label, { exact: true }));
  await humanFill(page, field, value);
});

When(
  "I type {string} into {string} and press Enter",
  async ({ page }, message: string, placeholder: string) => {
    const input = page.getByPlaceholder(placeholder, { exact: true });
    await humanFill(page, input, message);
    await humanPress(page, input, "Enter");
  },
);

Given("I clear local storage keys {string}", async ({ page }, keysCsv: string) => {
  const keys = keysCsv.split(",").map((k) => k.trim()).filter(Boolean);
  await page.evaluate((list) => {
    for (const key of list) localStorage.removeItem(key);
  }, keys);
  await page.reload();
  await humanPause(page);
  if (page.url().includes("/realms/") && scenarioState.signedInAs) {
    const { username, password } = credentialsForUser(scenarioState.signedInAs);
    await loginViaKeycloak(page, username, password);
  }
});

Then("I should see {string}", async ({ page }, text: string) => {
  await expect(page.getByText(text, { exact: true }).first()).toBeVisible();
});

Then("I should not see {string}", async ({ page }, text: string) => {
  await expect(page.getByText(text, { exact: true })).toHaveCount(0);
});

Then("I should see the button {string}", async ({ page }, name: string) => {
  await expect(page.getByRole("button", { name, exact: true })).toBeVisible();
});

Then("I should not see the button {string}", async ({ page }, name: string) => {
  await expect(page.getByRole("button", { name, exact: true })).toHaveCount(0);
});

Then("I should see the heading {string}", async ({ page }, name: string) => {
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
});

Then("I should see the placeholder {string}", async ({ page }, placeholder: string) => {
  await expect(page.getByPlaceholder(placeholder, { exact: true })).toBeVisible();
});

Then("I should be on {string}", async ({ page }, path: string) => {
  const escaped = path.replace("/", "\\/");
  await expect(page).toHaveURL(new RegExp(`${escaped}\\/?(\\?|#|$)`));
});

Then("I should be on a page matching {string}", async ({ page }, pattern: string) => {
  await expect(page).toHaveURL(new RegExp(pattern));
});

Then("the page theme should be {string}", async ({ page }, theme: string) => {
  await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
});

Then("local storage {string} should be {string}", async ({ page }, key: string, value: string) => {
  const stored = await page.evaluate((k) => localStorage.getItem(k), key);
  expect(stored).toBe(value);
});

Then("I should see the username {string}", async ({ page }, username: string) => {
  await expect(page.locator(".profile-menu-name")).toContainText(username, { ignoreCase: true });
});
