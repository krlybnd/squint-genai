import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";
import { test } from "../support/fixtures";
import { collectOnScreen, callJudge, logVerdict, appendJudgeReport } from "../support/judge";
import { lastSseTrace } from "../support/sse-tap";

const { Then } = createBdd(test);

Then("the on-screen answer is judged:", async ({ page }, checklist: string) => {
  const screen = await collectOnScreen(page);
  if (!screen.assistant && !screen.error) {
    console.error("MISMATCH: nothing on screen to judge (no assistant reply, no comment error).");
    expect(screen.assistant || screen.error, "MISMATCH: nothing on screen to judge").toBeTruthy();
    return;
  }

  const trace = await lastSseTrace(page);
  const label = checklist.trim().split("\n")[0]?.slice(0, 80) || "judge";

  let verdict;
  try {
    verdict = await callJudge({ checklist, screen, trace });
  } catch (err) {
    const reason = err instanceof Error ? err.message : String(err);
    console.error(`MISMATCH: judge call failed — ${reason}`);
    appendJudgeReport({
      label,
      checklist,
      screen,
      trace,
      verdict: { ok: false, reason: `judge call failed — ${reason}`, model: "judge" },
    });
    throw err;
  }

  logVerdict(verdict);
  appendJudgeReport({ label, checklist, screen, trace, verdict });

  expect(verdict.ok, `MISMATCH: ${verdict.reason}`).toBe(true);
});
