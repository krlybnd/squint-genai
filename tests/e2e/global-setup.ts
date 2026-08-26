import type { FullConfig } from "@playwright/test";
import fs from "node:fs";

/** Per-scenario Keycloak login runs in steps (see support/keycloak-login.ts). */
export default async function globalSetup(_config: FullConfig): Promise<void> {
  fs.mkdirSync(".auth", { recursive: true });
}
