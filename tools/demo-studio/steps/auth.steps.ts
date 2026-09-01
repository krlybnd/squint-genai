import { createBdd } from "playwright-bdd";
import { expect, test } from "../support/fixtures";
import { humanGoto } from "../support/human";
import { ensureLoggedInUser } from "../support/keycloak-login";
import { scenarioState } from "../support/scenario-state";

const { Given } = createBdd(test);

Given("I am signed in as {string}", async ({ page }, who: string) => {
  scenarioState.signedInAs = who;
  await ensureLoggedInUser(page, who);
  await expect(page.locator(".profile-menu-name")).toBeVisible();
  if (process.env.DEMO_AUTH === "0") {
    await humanGoto(page, "/");
  }
});
