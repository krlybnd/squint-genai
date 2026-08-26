import { createBdd } from "playwright-bdd";
import { humanClick } from "../support/human";
import { expect, test } from "../support/fixtures";

const { When, Then } = createBdd(test);

Then("I should see admin section {string}", async ({ page }, section: string) => {
  await expect(page.getByRole("button", { name: section })).toBeVisible();
});

When("I select admin section {string}", async ({ page }, section: string) => {
  await humanClick(page, page.getByRole("button", { name: section }));
});

Then("the admin users table or list should be visible", async ({ page }) => {
  await expect(page.locator(".admin-resource-panel").first()).toBeVisible();
});

Then("I should not see the admin tenants management UI", async ({ page }) => {
  await expect(page.locator(".admin-nav-panel")).toHaveCount(0);
});

Then("I should be redirected to the main chat view or see access denied", async ({ page }) => {
  await expect(page).toHaveURL(/\/(\?|$)/);
  await expect(page.locator(".chat-panel")).toBeVisible();
});

Then("the admin tenants list should be visible", async ({ page }) => {
  await expect(page.locator(".admin-resource-panel")).toBeVisible();
});
