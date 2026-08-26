import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const configPath = resolve(process.argv[2] ?? "public/config.json");
const config = JSON.parse(readFileSync(configPath, "utf8"));

config.auth ??= {};
config.auth.enabled = process.env.VITE_AUTH_ENABLED === "true";
if (process.env.VITE_KEYCLOAK_URL) {
  config.auth.keycloakUrl = process.env.VITE_KEYCLOAK_URL;
}
if (process.env.VITE_KEYCLOAK_REALM) {
  config.auth.keycloakRealm = process.env.VITE_KEYCLOAK_REALM;
}
if (process.env.VITE_KEYCLOAK_CLIENT_ID) {
  config.auth.keycloakClientId = process.env.VITE_KEYCLOAK_CLIENT_ID;
}

writeFileSync(configPath, `${JSON.stringify(config, null, 2)}\n`);
