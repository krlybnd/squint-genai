import type { Page } from "@playwright/test";
import { humanClick, humanFill, humanGoto } from "./human";

export type E2ePersona = "default" | "readonly" | "nonAdmin";

function keycloakSubmit(page: Page) {
  return page.locator("#kc-login, input[type='submit']").or(
    page.getByRole("button", { name: /sign in/i }),
  );
}

function keycloakUsername(page: Page) {
  return page.locator("#username").or(page.getByRole("textbox", { name: /username|email/i }));
}

function keycloakPassword(page: Page) {
  return page.locator("#password").or(page.getByRole("textbox", { name: /^password$/i }));
}

async function isAppAuthenticated(page: Page): Promise<boolean> {
  return page.locator(".profile-menu-name").isVisible();
}

/** Wait until Keycloak redirect finished or the app is already authenticated. */
async function waitForAuthGate(page: Page): Promise<void> {
  await page.waitForFunction(
    () => {
      const onKeycloak = window.location.pathname.includes("/realms/");
      const hasProfile = !!document.querySelector(".profile-menu-name");
      const hasDocuments = !!document.querySelector(".documents-panel");
      return onKeycloak || hasProfile || hasDocuments;
    },
    { timeout: 60_000 },
  );
}

export function e2eCredentials(persona: E2ePersona = "default"): { username: string; password: string } {
  switch (persona) {
    case "readonly":
      return {
        username: process.env.E2E_READONLY_USER ?? "bob@tenant-b.local",
        password: process.env.E2E_READONLY_PASSWORD ?? "bob",
      };
    case "nonAdmin":
      return {
        username: process.env.E2E_NON_ADMIN_USER ?? "writer@tenant-a.local",
        password: process.env.E2E_NON_ADMIN_PASSWORD ?? "writer",
      };
    default:
      return {
        username: process.env.E2E_USER ?? "admin",
        password: process.env.E2E_PASSWORD ?? "admin",
      };
  }
}

export async function loginViaKeycloak(
  page: Page,
  username: string,
  password: string,
): Promise<void> {
  await page.waitForURL(/\/realms\//, { timeout: 60_000 });

  const userInput = keycloakUsername(page);
  await userInput.waitFor({ state: "visible", timeout: 30_000 });
  await humanFill(page, userInput, username);
  await humanClick(page, keycloakSubmit(page).first());

  const passwordInput = keycloakPassword(page);
  await passwordInput.waitFor({ state: "visible", timeout: 30_000 });
  await humanFill(page, passwordInput, password);
  await humanClick(page, keycloakSubmit(page).first());

  await page.waitForURL(
    (url) => url.hostname === "localhost" && !url.pathname.includes("/realms/"),
    { timeout: 60_000 },
  );
  await page.locator(".profile-menu-name").waitFor({ timeout: 30_000 });
}

export async function signOutIfAuthenticated(page: Page): Promise<void> {
  if (process.env.E2E_AUTH === "0") return;
  if (!(await isAppAuthenticated(page))) return;

  await humanClick(page, page.locator(".profile-menu-trigger"));
  await humanClick(page, page.getByRole("menuitem", { name: /log out|kijelentkezés|abmelden/i }));
  await page.waitForFunction(
    () => window.location.pathname.includes("/realms/") || !document.querySelector(".profile-menu-name"),
    { timeout: 30_000 },
  );
}

export async function ensureLoggedInAs(
  page: Page,
  persona: E2ePersona = "default",
): Promise<void> {
  const { username, password } = e2eCredentials(persona);
  await humanGoto(page, "/");
  if (process.env.E2E_AUTH === "0") {
    return;
  }

  await waitForAuthGate(page);
  if (await isAppAuthenticated(page)) {
    await signOutIfAuthenticated(page);
  }

  await humanGoto(page, "/");
  await waitForAuthGate(page);
  if (await isAppAuthenticated(page)) {
    await page.context().clearCookies();
    await humanGoto(page, "/");
    await waitForAuthGate(page);
  }

  if (!(await isAppAuthenticated(page))) {
    await loginViaKeycloak(page, username, password);
  }
}

export async function ensureLoggedIn(page: Page): Promise<void> {
  await ensureLoggedInAs(page, "default");
}
