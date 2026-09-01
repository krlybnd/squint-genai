import { walkthrough } from "./walkthrough";

/** Locator/click timeout. Missing UI must fail here — not at the scenario timeout. */
export const ACTION_TIMEOUT_MS = Number(process.env.DEMO_ACTION_TIMEOUT_MS ?? 15_000);
export const NAV_TIMEOUT_MS = Number(process.env.DEMO_NAV_TIMEOUT_MS ?? 20_000);
export const EXPECT_TIMEOUT_MS = Number(process.env.DEMO_EXPECT_TIMEOUT_MS ?? 12_000);

const DEFAULT_STEP_MS = Number(process.env.DEMO_STEP_TIMEOUT_MS ?? 20_000);

/** Own budget from the step title (caption hold is added separately). */
function ownBudgetMs(title: string): number {
  const within = title.match(/within (\d+) seconds/i);
  if (within) return Number(within[1]) * 1000 + 5_000;
  if (/signed in as/i.test(title)) return 70_000;
  if (/generation has stopped/i.test(title)) return 100_000;
  if (/documents list is empty/i.test(title)) return 180_000;
  if (/comment error|Save comment/i.test(title)) return 70_000;
  if (/on-screen answer is judged/i.test(title)) return 90_000;
  const waitSec = title.match(/I wait (\d+) seconds/i);
  if (waitSec) return Number(waitSec[1]) * 1000 + 5_000;
  if (/the caption is /i.test(title)) {
    const holds = title.match(/\(([\d,\s]+)\)\s*$/)?.[1];
    const sum = holds
      ? holds.split(",").reduce((s, n) => s + Number(n.trim()), 0)
      : 20;
    return sum * 1000 + 8_000;
  }
  if (/I go to /i.test(title)) return NAV_TIMEOUT_MS + 8_000;
  if (/I open the /i.test(title)) return 15_000;
  return DEFAULT_STEP_MS;
}

/** Watchdog budget for one Gherkin step. Includes leftover caption hold (waited on the next step). */
export function stepBudgetMs(title: string): number {
  return ownBudgetMs(title) + walkthrough.remainingHoldMs() + 5_000;
}
