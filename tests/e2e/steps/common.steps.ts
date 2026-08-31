import { createBdd } from "playwright-bdd";
import { humanGoto, humanPause } from "../support/human";
import { ensureLoggedIn } from "../support/keycloak-login";
import { expect, test } from "../support/fixtures";

const { Given, When, Then } = createBdd(test);

Given("the application is running with authentication enabled", async ({ page }) => {
  await ensureLoggedIn(page);
  if (process.env.E2E_AUTH === "0") {
    await expect(page.getByRole("heading", { name: "Documents", exact: true })).toBeVisible();
    return;
  }
  await expect(page.locator(".documents-panel")).toBeVisible();
});

When("I navigate to {string}", async ({ page }, path: string) => {
  await humanGoto(page, path);
});

Given("local storage is cleared for locale and theme", async ({ page }) => {
  await ensureLoggedIn(page);
  await page.evaluate(() => {
    localStorage.removeItem("app-locale");
    localStorage.removeItem("app-theme");
  });
  await page.reload();
  await humanPause(page);
  if (page.url().includes("/realms/")) {
    await ensureLoggedIn(page);
  }
});

Then("the document root should have theme {string}", async ({ page }, theme: string) => {
  await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
});

Then(
  "local storage key {string} should be {string}",
  async ({ page }, key: string, value: string) => {
    const stored = await page.evaluate((k) => localStorage.getItem(k), key);
    expect(stored).toBe(value);
  },
);

Then("I should be on path {string}", async ({ page }, path: string) => {
  const escaped = path.replace("/", "\\/");
  await expect(page).toHaveURL(new RegExp(`${escaped}\\/?(\\?|#|$)`));
});

Then("I should be on the Keycloak login page", async ({ page }) => {
  await expect(page).toHaveURL(/\/realms\//);
});

Then("the profile menu trigger should show my username", async ({ page }) => {
  const user = process.env.E2E_USER ?? "admin";
  await expect(page.locator(".profile-menu-name")).toContainText(user, { ignoreCase: true });
});
