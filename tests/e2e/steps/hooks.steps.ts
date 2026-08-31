import { createBdd } from "playwright-bdd";
import { test } from "../support/fixtures";
import { resetScenarioState } from "../support/scenario-state";
import { markScenarioStart, padScenarioToMinimum } from "../support/timing";

const { Before, After } = createBdd(test);

Before(async () => {
  resetScenarioState();
  markScenarioStart();
});

After(async ({ page }) => {
  await padScenarioToMinimum(page);
});
