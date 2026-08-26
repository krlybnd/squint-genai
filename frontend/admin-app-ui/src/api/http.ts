export { buildHeaders, buildHeadersAsync } from "@are/ui-core/http";
import { getEndpoint } from "@are/ui-core/app/appConfigStore";

export { getEndpoint };

export function adminBase(): string {
  return getEndpoint("admin");
}
