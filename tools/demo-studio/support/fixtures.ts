import fs from "node:fs";
import path from "node:path";
import { test as bddTest } from "playwright-bdd";
import { cursorInitScript } from "./cursor";
import { publishWalkthrough, walkthroughDir } from "./publish";
import { sseInitScript } from "./sse-tap";
import { ACTION_TIMEOUT_MS, NAV_TIMEOUT_MS } from "./timeouts";
import { isRecording, walkthrough } from "./walkthrough";

export const test = bddTest.extend({
  context: async ({ context }, use) => {
    await context.addInitScript(sseInitScript);
    if (isRecording()) {
      walkthrough.reset(Date.now());
      await context.addInitScript(cursorInitScript);
      await context.addInitScript(() => {
        localStorage.setItem("app-theme", "moon");
        document.documentElement.setAttribute("data-theme", "moon");
      });
    }
    await use(context);
  },
  page: async ({ page }, use, testInfo) => {
    page.setDefaultTimeout(ACTION_TIMEOUT_MS);
    page.setDefaultNavigationTimeout(NAV_TIMEOUT_MS);
    await use(page);
    if (!isRecording()) return;
    await walkthrough.finishCurrent(page);
    const video = page.video();
    await page.close();
    fs.mkdirSync(walkthroughDir, { recursive: true });
    if (video) {
      await video.saveAs(path.join(walkthroughDir, "video.webm"));
    }
    publishWalkthrough(testInfo.outputDir);
  },
});

export { expect } from "@playwright/test";
