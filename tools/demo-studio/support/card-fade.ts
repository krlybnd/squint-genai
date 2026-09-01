import type { Page } from "@playwright/test";
import { walkthrough } from "./walkthrough";

/** Black crossfade between file:// title cards (and off the last card into the app). */
export const CARD_FADE_MS = 900;

const CARD_ROOT = "[data-banner-card], [data-title-card], [data-summary], [data-agenda]";

export async function fadeCardOut(page: Page): Promise<void> {
  if ((await page.locator(CARD_ROOT).count()) === 0) return;
  await page.evaluate((ms) => {
    const existing = document.querySelector("[data-card-fade]");
    if (existing) return;
    const el = document.createElement("div");
    el.setAttribute("data-card-fade", "");
    el.style.cssText = [
      "position:fixed",
      "inset:0",
      "background:#000",
      "opacity:0",
      "z-index:99999",
      "pointer-events:none",
      `transition:opacity ${ms}ms ease`,
    ].join(";");
    document.body.appendChild(el);
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        el.style.opacity = "1";
      });
    });
  }, CARD_FADE_MS);
  await page.waitForTimeout(CARD_FADE_MS + 80);
}

/** Hold the current caption on this card, fade to black, then the caller navigates. */
export async function leaveCard(page: Page): Promise<void> {
  await walkthrough.finishCurrent(page);
  await fadeCardOut(page);
}
