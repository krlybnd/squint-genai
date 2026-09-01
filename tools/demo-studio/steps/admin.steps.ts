import { createBdd } from "playwright-bdd";
import { expect, test } from "../support/fixtures";
import { humanClick } from "../support/human";
import { scenarioState } from "../support/scenario-state";

const { When } = createBdd(test);

function adminModal(page: import("@playwright/test").Page) {
  return page.locator(".app-modal");
}

function membershipRow(page: import("@playwright/test").Page, rowText: string) {
  return adminModal(page).locator(".admin-membership-row").filter({ hasText: rowText });
}

function roleCheckbox(row: import("@playwright/test").Locator, role: string) {
  return row.locator("label.ui-checkbox").filter({ hasText: new RegExp(`^${role}$`, "i") }).locator("input");
}

async function selectAssignOption(
  page: import("@playwright/test").Page,
  optionText: string,
): Promise<string> {
  const modal = adminModal(page);
  await humanClick(page, modal.getByRole("button", { name: /assign organisation/i }));
  const option = page.getByRole("option", { name: new RegExp(optionText, "i") }).first();
  await expect(option).toBeVisible();
  const label = ((await option.textContent()) ?? optionText).trim();
  await humanClick(page, option);
  return label;
}

When("I open the row {string}", async ({ page }, text: string) => {
  const row = page.locator(".admin-resource-row").filter({ hasText: text });
  await expect(row).toBeVisible();
  await row.dblclick();
  await expect(adminModal(page)).toBeVisible();
});

When("I assign the tenant {string}", async ({ page }, tenant: string) => {
  const modal = adminModal(page);
  const existing = membershipRow(page, tenant);
  if ((await existing.count()) > 0) {
    scenarioState.tenantAlias = tenant;
    return;
  }
  const label = await selectAssignOption(page, tenant);
  scenarioState.tenantAlias = label.includes("—") ? label.split("—")[0].trim() : tenant;
  await humanClick(page, modal.getByRole("button", { name: "Add", exact: true }));
  await expect(membershipRow(page, scenarioState.tenantAlias).or(membershipRow(page, tenant))).toBeVisible({
    timeout: 30_000,
  });
});

When("I set membership roles {string}", async ({ page }, rolesCsv: string) => {
  const row = membershipRow(page, scenarioState.tenantAlias).or(membershipRow(page, "Tenant B"));
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
    const cancel = modal.getByRole("button", { name: "Cancel", exact: true });
    if ((await cancel.count()) > 0) {
      await humanClick(page, cancel);
    } else {
      await humanClick(page, modal.getByRole("button", { name: "Close", exact: true }));
    }
  }
  await expect(modal).toHaveCount(0);
});
