import { createBdd } from "playwright-bdd";
import { humanClick, humanFill } from "../support/human";
import { scenarioState } from "../support/scenario-state";
import { expect, test } from "../support/fixtures";

const { When, Then } = createBdd(test);

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
  triggerName: string,
  optionText: string,
) {
  await humanClick(page, scope.getByRole("button", { name: triggerName, exact: true }));
  await humanClick(page, scope.getByRole("option", { name: optionText }));
}

When(
  "I create a unique tenant with alias prefix {string} and name prefix {string}",
  async ({ page }, aliasPrefix: string, namePrefix: string) => {
    scenarioState.tenantAlias = `${aliasPrefix}-${Date.now()}`;
    scenarioState.tenantName = `${namePrefix} ${scenarioState.tenantAlias}`;

    await humanClick(page, page.getByRole("button", { name: "New tenant", exact: true }));
    const modal = adminModal(page);
    await expect(modal).toBeVisible();
    await humanFill(page, modal.getByLabel("Alias", { exact: true }), scenarioState.tenantAlias);
    await humanFill(page, modal.getByLabel("Display name", { exact: true }), scenarioState.tenantName);
    await humanClick(page, modal.getByRole("button", { name: "Save", exact: true }));
    await expect(modal).toHaveCount(0);
    await expect(page.locator(".admin-resource-row").filter({ hasText: scenarioState.tenantAlias })).toBeVisible();
  },
);

When("I open the row {string}", async ({ page }, text: string) => {
  const row = page.locator(".admin-resource-row").filter({ hasText: text });
  await expect(row).toBeVisible();
  await row.dblclick();
  await expect(adminModal(page)).toBeVisible();
});

When("I assign the last created tenant", async ({ page }) => {
  const modal = adminModal(page);
  await selectUiOption(page, modal, "Assign tenant", scenarioState.tenantAlias);
  await humanClick(page, modal.getByRole("button", { name: "Add", exact: true }));
  await expect(membershipRow(page, scenarioState.tenantAlias)).toBeVisible({ timeout: 30_000 });
});

When("I set membership roles {string}", async ({ page }, rolesCsv: string) => {
  const row = membershipRow(page, scenarioState.tenantAlias);
  for (const role of rolesCsv.split(",").map((r) => r.trim()).filter(Boolean)) {
    const checkbox = roleCheckbox(row, role);
    if (!(await checkbox.isChecked())) {
      const roleSave = page.waitForResponse(
        (resp) => resp.request().method() === "PUT" && resp.url().includes("/roles") && resp.ok(),
      );
      await humanClick(page, row.locator("label.ui-checkbox").filter({ hasText: new RegExp(`^${role}$`, "i") }));
      await roleSave;
    }
    await expect(checkbox).toBeChecked({ timeout: 30_000 });
  }
});

When("I close the dialog", async ({ page }) => {
  const modal = adminModal(page);
  if (await modal.isVisible()) {
    await humanClick(page, modal.getByRole("button", { name: "Cancel", exact: true }));
  }
  await expect(modal).toHaveCount(0);
});

When("I open the last created tenant", async ({ page }) => {
  const membersLoad = page.waitForResponse(
    (resp) => resp.request().method() === "GET" && resp.url().includes("/members") && resp.ok(),
  );
  const row = page.locator(".admin-resource-row").filter({ hasText: scenarioState.tenantAlias });
  await expect(row).toBeVisible();
  await row.dblclick();
  await expect(adminModal(page)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Edit tenant", exact: true })).toBeVisible();
  await membersLoad;
});

Then(
  "the member {string} should have roles {string}",
  async ({ page }, username: string, rolesCsv: string) => {
    const row = membershipRow(page, username);
    await expect(row).toBeVisible({ timeout: 30_000 });
    for (const role of rolesCsv.split(",").map((r) => r.trim()).filter(Boolean)) {
      await expect(roleCheckbox(row, role)).toBeChecked();
    }
  },
);
