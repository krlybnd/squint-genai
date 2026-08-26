import type { Page } from "@playwright/test";
import { humanClick, humanFill, humanGoto } from "./human";

export async function loginViaKeycloak(
  page: Page,
  username: string,
  password: string,
): Promise<void> {
  if (!page.url().includes("/realms/")) {
    return;
  }
  const userInput = page.locator("#username");
  if (await userInput.isVisible()) {
    await humanFill(page, userInput, username);
    await humanClick(page, page.locator("#kc-login, input[type='submit']").first());
  }
  const passwordInput = page.locator("#password");
  await passwordInput.waitFor({ timeout: 30_000 });
  await humanFill(page, passwordInput, password);
  await humanClick(page, page.locator("#kc-login, input[type='submit']").first());
  await page.waitForURL(
    (url) => url.hostname === "localhost" && !url.pathname.includes("/realms/"),
    { timeout: 60_000 },
  );
  await page.locator(".profile-menu-name").waitFor({ timeout: 30_000 });
}

export async function ensureLoggedIn(page: Page): Promise<void> {
  const username = process.env.E2E_USER ?? "admin";
  const password = process.env.E2E_PASSWORD ?? "admin";
  await humanGoto(page, "/");
  if (process.env.E2E_AUTH === "0") {
    return;
  }
  await loginViaKeycloak(page, username, password);
}

export function e2eCredentials(): { username: string; password: string } {
  return {
    username: process.env.E2E_USER ?? "admin",
    password: process.env.E2E_PASSWORD ?? "admin",
  };
}
