export const scenarioState = {
  signedInAs: "",
  tenantAlias: "",
  tenantName: "",
};

export function resetScenarioState(): void {
  scenarioState.signedInAs = "";
  scenarioState.tenantAlias = "";
  scenarioState.tenantName = "";
}
