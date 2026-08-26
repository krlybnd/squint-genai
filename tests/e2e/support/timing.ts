import type { Page } from "@playwright/test";

let scenarioStartMs = Date.now();

export function markScenarioStart(): void {
  scenarioStartMs = Date.now();
}

export function minScenarioMs(): number {
  return Number(process.env.E2E_MIN_SCENARIO_MS ?? 0);
}

/** Optional pad so demo videos reach a minimum length (E2E_MIN_SCENARIO_MS > 0). */
export async function padScenarioToMinimum(page: Page): Promise<void> {
  const remaining = minScenarioMs() - (Date.now() - scenarioStartMs);
  if (remaining > 0) {
    await page.waitForTimeout(remaining);
  }
}
