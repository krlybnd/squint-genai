import type { Locator, Page } from "@playwright/test";

const humanMode = process.env.E2E_HUMAN === "1";

function mouseSteps(): number {
  return humanMode ? Number(process.env.E2E_MOUSE_STEPS ?? 35) : 1;
}

function pauseMs(): number {
  return humanMode ? Number(process.env.E2E_PAUSE_MS ?? 400) : 0;
}

function typingDelayMs(): number {
  return humanMode ? Number(process.env.E2E_TYPING_DELAY_MS ?? 50) : 0;
}

export async function humanPause(page: Page, ms = pauseMs()): Promise<void> {
  if (ms <= 0) return;
  await page.waitForTimeout(ms);
}

/** Move pointer to the element center, then click. Smooth steps only in E2E_HUMAN mode. */
export async function humanClick(page: Page, target: Locator): Promise<void> {
  await target.waitFor({ state: "visible" });
  await target.scrollIntoViewIfNeeded();
  await humanPause(page, humanMode ? pauseMs() / 2 : 0);
  const box = await target.boundingBox();
  if (!box || !humanMode) {
    await target.click();
    await humanPause(page);
    return;
  }
  const x = box.x + box.width / 2;
  const y = box.y + box.height / 2;
  await page.mouse.move(x, y, { steps: mouseSteps() });
  await humanPause(page);
  await page.mouse.down();
  await page.waitForTimeout(80);
  await page.mouse.up();
  await humanPause(page);
}

export async function humanFill(page: Page, target: Locator, text: string): Promise<void> {
  if (!humanMode) {
    await target.fill(text);
    return;
  }
  await humanClick(page, target);
  await target.fill("");
  await humanPause(page, 200);
  await target.pressSequentially(text, { delay: typingDelayMs() });
  await humanPause(page);
}

export async function humanPress(page: Page, target: Locator, key: string): Promise<void> {
  if (!humanMode) {
    await target.press(key);
    return;
  }
  await humanClick(page, target);
  await page.keyboard.press(key, { delay: typingDelayMs() });
  await humanPause(page);
}

export async function humanGoto(page: Page, url: string): Promise<void> {
  await page.goto(url);
  await humanPause(page, humanMode ? pauseMs() * 2 : 0);
}
