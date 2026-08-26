import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

const appRoot = process.cwd();
const repoRoot = resolve(appRoot, "../..");
const outDir = resolve(appRoot, "src/generated");

const SPECS = [
  { name: "api", out: "schema-api.d.ts", pathsExport: "ApiPaths", componentsExport: "ApiComponents" },
  { name: "chat", out: "schema-chat.d.ts", pathsExport: "ChatPaths", componentsExport: "ChatComponents" },
  { name: "admin", out: "schema-admin.d.ts", pathsExport: "AdminPaths", componentsExport: "AdminComponents" },
];

mkdirSync(outDir, { recursive: true });

for (const spec of SPECS) {
  const file = resolve(repoRoot, "openapi", `${spec.name}.yaml`);
  if (!existsSync(file)) {
    console.error(`Missing openapi/${spec.name}.yaml — run \`make generate-openapi\` first.`);
    process.exit(1);
  }
  const result = spawnSync(
    "npx",
    [
      "openapi-typescript",
      file,
      "-o",
      resolve(outDir, spec.out),
      "--export-type",
      "--path-params-as-types",
    ],
    { stdio: "inherit", shell: true },
  );
  if ((result.status ?? 1) !== 0) {
    process.exit(result.status ?? 1);
  }
}

const index = SPECS.map(
  (spec) =>
    `export type { paths as ${spec.pathsExport}, components as ${spec.componentsExport} } from "./${spec.out.replace(".d.ts", "")}";`,
).join("\n") + "\n";

writeFileSync(resolve(outDir, "index.ts"), index, "utf-8");
