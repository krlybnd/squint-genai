import path from "node:path";

type VitestReportOptions = {
  appDir: string;
  projectName: string;
};

/** Route Vitest JUnit + coverage HTML under repo-root .reports/node/<projectName>/. */
export function vitestNodeReportConfig({ appDir, projectName }: VitestReportOptions) {
  const repoRoot = path.resolve(appDir, "../..");
  const reportDir = path.join(repoRoot, ".reports", "node", projectName);

  return {
    reporters: ["default", ["junit", { outputFile: path.join(reportDir, "unit-test.xml") }]] as const,
    coverage: {
      reportsDirectory: path.join(reportDir, "coverage"),
    },
  };
}
