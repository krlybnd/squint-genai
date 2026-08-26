import { createBdd } from "playwright-bdd";
import { test } from "../support/fixtures";
import { markScenarioStart, padScenarioToMinimum } from "../support/timing";

const { Before, After } = createBdd(test);

Before(async () => {
  markScenarioStart();
});

After(async ({ page }) => {
  await padScenarioToMinimum(page);
});
