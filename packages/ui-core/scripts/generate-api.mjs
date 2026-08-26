import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

const appRoot = process.cwd();
const repoRoot = resolve(appRoot, "../..");

const specArg = process.env.API_SPECS?.trim();
const defaultSpecs = process.env.APP_NAME === "admin" ? "admin" : "api,chat";

const SPEC_MAP = {
  api: { name: "api", out: "schema-api.d.ts", exportName: "ApiComponents" },
  chat: { name: "chat", out: "schema-chat.d.ts", exportName: "ChatComponents" },
  admin: { name: "admin", out: "schema-admin.d.ts", exportName: "AdminComponents" },
};

const selected = (specArg ?? defaultSpecs).split(",").map((s) => s.trim()).filter(Boolean);
const outDir = resolve(appRoot, "src/api/generated");

function resolveOpenapiFile(name) {
  const candidates = [
    resolve(repoRoot, "openapi", `${name}.yaml`),
    resolve("/openapi", `${name}.yaml`),
  ];
  for (const candidate of candidates) {
    if (existsSync(candidate)) {
      return candidate;
    }
  }
  return resolve(repoRoot, "openapi", `${name}.yaml`);
}

const FALLBACK = `/** Fallback stub — run \`make sync\` then \`npm run generate:api\` for real types. */
export interface components {
  schemas: Record<string, unknown>;
}
`;

mkdirSync(outDir, { recursive: true });

const specs = selected.map((key) => {
  const meta = SPEC_MAP[key];
  if (!meta) {
    console.error(`Unknown API spec: ${key}`);
    process.exit(1);
  }
  return { ...meta, file: resolveOpenapiFile(meta.name) };
});

let missing = false;
for (const { name, file } of specs) {
  if (!existsSync(file)) {
    console.warn(`openapi/${name}.yaml not found — run \`make sync\` first.`);
    missing = true;
  }
}

const indexExports =
  specs.map(({ out, exportName }) => `export type { components as ${exportName} } from "./${out.replace(".d.ts", "")}";`).join("\n") +
  "\n";

if (missing) {
  for (const { out } of specs) {
    writeFileSync(resolve(outDir, out), FALLBACK, "utf-8");
  }
  writeFileSync(resolve(outDir, "index.ts"), indexExports, "utf-8");
  process.exit(0);
}

for (const { file, out } of specs) {
  const result = spawnSync(
    "npx",
    [
      "openapi-typescript",
      file,
      "-o",
      resolve(outDir, out),
      "--export-type",
      "--path-params-as-types",
    ],
    { stdio: "inherit", shell: true },
  );
  if ((result.status ?? 1) !== 0) {
    process.exit(result.status ?? 1);
  }
}

writeFileSync(resolve(outDir, "index.ts"), indexExports, "utf-8");
