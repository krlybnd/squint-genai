export { buildHeaders, buildHeadersAsync } from "@are/ui-core/http";
import { getEndpoint } from "@are/ui-core/app/appConfigStore";

export { getEndpoint };

export function apiBase(): string {
  return getEndpoint("api");
}

export function chatBase(): string {
  return getEndpoint("chat");
}
