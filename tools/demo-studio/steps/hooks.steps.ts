import { createBdd } from "playwright-bdd";
import { test } from "../support/fixtures";
import { resetJudgeReport } from "../support/judge";
import { resetSseTap } from "../support/sse-tap";
import { resetScenarioState } from "../support/scenario-state";
import { stepBudgetMs } from "../support/timeouts";
import { isRecording, walkthrough } from "../support/walkthrough";

const { Before, After, BeforeStep, AfterStep } = createBdd(test);

let watchdog: ReturnType<typeof setTimeout> | undefined;

function clearWatchdog(): void {
  if (watchdog) {
    clearTimeout(watchdog);
    watchdog = undefined;
  }
}

Before(async () => {
  resetScenarioState();
});

Before({ tags: "@demo" }, async () => {
  resetJudgeReport();
  resetSseTap();
});

BeforeStep(async ({ page, $step }) => {
  clearWatchdog();
  const title = $step.title;
  const budget = stepBudgetMs(title);
  console.log(`→ ${title}`);
  watchdog = setTimeout(() => {
    console.error(`\nSTUCK — step exceeded ${Math.round(budget / 1000)}s:\n  ${title}\n`);
    void page.context().close().catch(() => {});
  }, budget);
});

AfterStep(async () => {
  clearWatchdog();
});

After(async ({ page }) => {
  clearWatchdog();
  if (isRecording()) {
    await walkthrough.finishCurrent(page);
  }
});
