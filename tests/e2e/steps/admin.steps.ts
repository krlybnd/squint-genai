import { createBdd } from "playwright-bdd";
import { humanClick, humanFill } from "../support/human";
import { expect, test } from "../support/fixtures";

const { When, Then } = createBdd(test);

/** Per-scenario tenant created in membership flow (workers: 1). */
let e2eTenantAlias = "";
let e2eTenantName = "";

const saveButton = /^(save|mentés|speichern)$/i;
const cancelButton = /^(cancel|mégse|abbrechen)$/i;
const newTenantButton = /new tenant|új bérlő|neuer mandant/i;
const addMemberButton = /^(add|hozzáadás|hinzufügen)$/i;
const assignTenantSelect = /assign tenant|bérlő hozzárendelés|mandant zuweisen/i;
const editUserHeading = /edit user|felhasználó szerkesztése|benutzer bearbeiten/i;
const editTenantHeading = /edit tenant|bérlő szerkesztése|mandant bearbeiten/i;

function adminModal(page: import("@playwright/test").Page) {
  return page.locator(".app-modal");
}

function membershipRow(page: import("@playwright/test").Page, rowText: string) {
  return adminModal(page).locator(".admin-membership-row").filter({ hasText: rowText });
}

function roleCheckbox(row: import("@playwright/test").Locator, role: string) {
  return row.locator("label.ui-checkbox").filter({ hasText: new RegExp(`^${role}$`, "i") }).locator("input");
}

async function selectUiOption(
  page: import("@playwright/test").Page,
  scope: import("@playwright/test").Locator,
  triggerName: RegExp,
  optionPattern: RegExp | string,
) {
  await humanClick(page, scope.getByRole("button", { name: triggerName }));
  const option =
    typeof optionPattern === "string"
      ? scope.getByRole("option", { name: optionPattern, exact: true })
      : scope.getByRole("option", { name: optionPattern });
  await humanClick(page, option);
}

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

When("I create a unique tenant for membership testing", async ({ page }) => {
  e2eTenantAlias = `e2e-${Date.now()}`;
  e2eTenantName = `E2E ${e2eTenantAlias}`;

  await humanClick(page, page.getByRole("button", { name: newTenantButton }));
  const modal = adminModal(page);
  await expect(modal).toBeVisible();

  await humanFill(page, modal.locator("#tenant-alias"), e2eTenantAlias);
  await humanFill(page, modal.locator("#tenant-name"), e2eTenantName);
  await humanClick(page, modal.getByRole("button", { name: saveButton }));

  await expect(modal).toHaveCount(0);
  await expect(page.locator(".admin-resource-row").filter({ hasText: e2eTenantAlias })).toBeVisible();
});

When("I open the admin user editor for {string}", async ({ page }, username: string) => {
  const row = page.locator(".admin-resource-row").filter({ hasText: username });
  await expect(row).toBeVisible();
  await row.dblclick();
  await expect(adminModal(page)).toBeVisible();
  await expect(page.getByRole("heading", { name: editUserHeading })).toBeVisible();
});

When("I assign the e2e tenant to the current user", async ({ page }) => {
  const modal = adminModal(page);
  await selectUiOption(page, modal, assignTenantSelect, new RegExp(e2eTenantAlias));
  await humanClick(page, modal.getByRole("button", { name: addMemberButton }));
  await expect(membershipRow(page, e2eTenantAlias)).toBeVisible({ timeout: 30_000 });
});

When(
  "I set roles {string} and {string} for the e2e tenant on the user membership",
  async ({ page }, role1: string, role2: string) => {
    const row = membershipRow(page, e2eTenantAlias);
    for (const role of [role1, role2]) {
      const checkbox = roleCheckbox(row, role);
      if (!(await checkbox.isChecked())) {
        const roleSave = page.waitForResponse(
          (resp) =>
            resp.request().method() === "PUT" &&
            resp.url().includes("/roles") &&
            resp.ok(),
        );
        await humanClick(page, row.locator("label.ui-checkbox").filter({ hasText: new RegExp(`^${role}$`, "i") }));
        await roleSave;
      }
      await expect(checkbox).toBeChecked({ timeout: 30_000 });
    }
  },
);

When("I close the admin modal", async ({ page }) => {
  const modal = adminModal(page);
  if (await modal.isVisible()) {
    await humanClick(page, modal.getByRole("button", { name: cancelButton }));
  }
  await expect(modal).toHaveCount(0);
});

When("I open the e2e tenant for editing", async ({ page }) => {
  const membersLoad = page.waitForResponse(
    (resp) => resp.request().method() === "GET" && resp.url().includes("/members") && resp.ok(),
  );
  const row = page.locator(".admin-resource-row").filter({ hasText: e2eTenantAlias });
  await expect(row).toBeVisible();
  await row.dblclick();
  await expect(adminModal(page)).toBeVisible();
  await expect(page.getByRole("heading", { name: editTenantHeading })).toBeVisible();
  await membersLoad;
});

Then(
  "the tenant members should include {string} with roles {string} and {string}",
  async ({ page }, username: string, role1: string, role2: string) => {
    const modal = adminModal(page);
    const row = membershipRow(page, username);
    await expect(row).toBeVisible({ timeout: 30_000 });
    await expect(roleCheckbox(row, role1)).toBeChecked();
    await expect(roleCheckbox(row, role2)).toBeChecked();
  },
);
