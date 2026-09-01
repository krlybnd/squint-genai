import { createBdd } from "playwright-bdd";
import { expect, test } from "../support/fixtures";
import { leaveCard } from "../support/card-fade";
import { humanClick, humanFill, humanGoto, humanPause, humanPress } from "../support/human";

const { When, Then } = createBdd(test);

When("I go to {string}", async ({ page }, path: string) => {
  await leaveCard(page);
  await humanGoto(page, path === "/admin" ? "/admin/" : path);
  if (path === "/") {
    await page
      .locator("#username, #kc-login, .documents-panel, .profile-menu-trigger")
      .or(page.getByRole("textbox", { name: /username or email/i }))
      .first()
      .waitFor({ state: "visible" });
  }
});

When("I click the button {string}", async ({ page }, name: string) => {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const profile = page.locator(".profile-menu-trigger").filter({
    has: page.locator(".profile-menu-name", { hasText: new RegExp(`^${escaped}$`, "i") }),
  });
  const exact = page.getByRole("button", { name, exact: true });
  const labeled = page.getByRole("button", { name: new RegExp(`^${escaped}(\\s|$)`, "i") });
  await humanClick(page, profile.or(exact).or(labeled).first());
});

When("I click the menu item {string}", async ({ page }, name: string) => {
  await humanClick(page, page.getByRole("menuitem", { name, exact: true }));
});

When("I choose {string}", async ({ page }, name: string) => {
  await humanClick(page, page.getByRole("menuitemradio", { name, exact: true }));
});

When("I close the profile menu", async ({ page }) => {
  const menu = page.locator(".profile-menu-dropdown");
  if ((await menu.count()) === 0 || !(await menu.isVisible())) return;
  await humanClick(page, page.locator(".profile-menu-trigger"));
  await expect(menu).toHaveCount(0);
});

When("I choose {string} from {string}", async ({ page }, option: string, trigger: string) => {
  const already = page.locator(".profile-menu-tenant", { hasText: option });
  if ((await already.count()) > 0 && (await already.first().isVisible())) {
    return;
  }
  const triggerBtn = page.getByRole("button", { name: trigger, exact: true });
  if ((await triggerBtn.count()) === 0 || !(await triggerBtn.first().isVisible())) {
    await humanClick(page, page.locator(".profile-menu-trigger"));
  }
  await humanClick(page, page.getByRole("button", { name: trigger, exact: true }));
  const exact = page.getByRole("option", { name: option, exact: true });
  if ((await exact.count()) > 0) {
    await humanClick(page, exact);
  } else {
    await humanClick(page, page.getByRole("option", { name: new RegExp(option, "i") }).first());
  }
  await expect(page.locator(".profile-menu-tenant")).toContainText(option, { timeout: 30_000 });
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

When("I reload the page", async ({ page }) => {
  await page.reload();
  await humanPause(page);
});
