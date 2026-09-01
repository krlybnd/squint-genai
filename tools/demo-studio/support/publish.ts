import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { walkthrough } from "./walkthrough";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const reportsDir = path.resolve(rootDir, "../../.reports/demo-studio");
export const walkthroughDir = path.join(reportsDir, "walkthrough");

function findWebm(dir: string): string | undefined {
  if (!fs.existsSync(dir)) return undefined;
  const stack = [dir];
  while (stack.length) {
    const current = stack.pop()!;
    for (const name of fs.readdirSync(current)) {
      const full = path.join(current, name);
      if (fs.statSync(full).isDirectory()) stack.push(full);
      else if (name.endsWith(".webm")) return full;
    }
  }
  return undefined;
}

export function publishWalkthrough(artifactDir: string): string {
  fs.mkdirSync(walkthroughDir, { recursive: true });
  walkthrough.writeTranscripts(walkthroughDir);
  walkthrough.writeTranscripts(artifactDir);

  const webm = findWebm(artifactDir);
  if (webm) {
    fs.copyFileSync(webm, path.join(walkthroughDir, "video.webm"));
  }
  return walkthroughDir;
}
