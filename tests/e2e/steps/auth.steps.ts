import { createBdd } from "playwright-bdd";
import { ensureLoggedInUser } from "../support/keycloak-login";
import { scenarioState } from "../support/scenario-state";
import { expect, test } from "../support/fixtures";
import { humanGoto } from "../support/human";

const { Given } = createBdd(test);

Given("I am signed in as {string}", async ({ page }, who: string) => {
  scenarioState.signedInAs = who;
  await ensureLoggedInUser(page, who);
  if (process.env.E2E_AUTH === "0") {
    await humanGoto(page, "/");
  }
  await expect(page.locator(".profile-menu-name")).toBeVisible();
});
