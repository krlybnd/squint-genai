import { createBdd } from "playwright-bdd";
import { humanClick, humanGoto, humanPause } from "../support/human";
import { ensureLoggedIn } from "../support/keycloak-login";
import { expect, test } from "../support/fixtures";

const { Given, When, Then } = createBdd(test);

Given("I am signed in as a user with write access", async ({ page }) => {
  await ensureLoggedIn(page);
  await expect(page.locator(".documents-panel")).toBeVisible();
});

Given("I am signed in as a read-only user", async ({ page }) => {
  test.skip(
    !process.env.E2E_READONLY_USER,
    "Set E2E_READONLY_USER and extend global-setup for a read-only persona",
  );
  await humanGoto(page, "/");
});

Given("I am signed in as a non-admin user with write access", async ({ page }) => {
  test.skip(
    !process.env.E2E_NON_ADMIN_USER,
    "Set E2E_NON_ADMIN_USER / E2E_NON_ADMIN_PASSWORD (realm user without admin role)",
  );
  await ensureLoggedIn(page);
  await expect(page.locator(".documents-panel")).toBeVisible();
});

Given("I am signed in as an administrator", async ({ page }) => {
  await ensureLoggedIn(page);
  await expect(page.locator(".profile-menu-trigger")).toBeVisible();
});

When("I open the account and preferences menu", async ({ page }) => {
  await humanClick(page, page.locator(".profile-menu-trigger"));
  await expect(page.getByRole("menu", { name: /account and preferences|fiók és beállítások/i })).toBeVisible();
});

When("I select language {string}", async ({ page }, languageLabel: string) => {
  await humanClick(page, page.getByRole("menuitemradio", { name: languageLabel }));
});

When("I select theme {string}", async ({ page }, themeLabel: string) => {
  await humanClick(page, page.getByRole("menuitemradio", { name: themeLabel }));
});

When("I reload the page", async ({ page }) => {
  await page.reload();
  await humanPause(page);
});

When("I sign out from the profile menu", async ({ page }) => {
  await humanClick(page, page.getByRole("menuitem", { name: /log out|kijelentkezés|abmelden/i }));
});

When("I follow the admin panel link", async ({ page }) => {
  await humanClick(page, page.getByRole("menuitem", { name: /admin panel|adminisztráció|verwaltung/i }));
});
