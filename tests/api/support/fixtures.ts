import { test as bddTest } from "playwright-bdd";

import {
  createAdminClient,
  createApiClient,
  createChatClient,
  type AdminClient,
  type ApiClient,
  type ChatClient,
} from "../src/clients";
import { optionalAdminAccessToken } from "../src/keycloak";
import type { AdminComponents, ApiComponents, ChatComponents } from "../src/generated";

export { expect } from "@playwright/test";

export type ChatSession = ChatComponents["schemas"]["ChatSessionOut"];
export type DocumentList = ApiComponents["schemas"]["DocumentListResponse"];
export type MeOut = ApiComponents["schemas"]["MeOut"];
export type TenantList = AdminComponents["schemas"]["TenantListResponse"];
export type UserList = AdminComponents["schemas"]["UserListResponse"];
export type AiSystemCard = ApiComponents["schemas"]["AiSystemCardOut"];

export type ScenarioMemory = {
  healthStatus?: string;
  documents?: DocumentList;
  session?: ChatSession;
  sessions?: ChatSession[];
  tenants?: TenantList;
  users?: UserList;
  chunkId?: string;
  sseEvents?: Array<{ event: string; data: Record<string, unknown> }>;
  commentStatus?: number;
  commentBody?: unknown;
  piiDocId?: string;
  piiSearchChunks?: Array<{ text: string; chunk_id?: string }>;
  piiVaultToken?: string;
  piiDetokenizeStatus?: number;
  piiDetokenizeBody?: unknown;
  httpStatus?: number;
  documentId?: string;
  me?: MeOut;
  systemCard?: AiSystemCard;
};

export const test = bddTest.extend<{
  api: ApiClient;
  chat: ChatClient;
  admin: AdminClient;
  memory: ScenarioMemory;
}>({
  api: async ({}, use) => {
    const bearer = await optionalAdminAccessToken();
    await use(createApiClient(bearer ? { bearer } : {}));
  },
  chat: async ({}, use) => {
    const bearer = await optionalAdminAccessToken();
    await use(createChatClient(bearer ? { bearer } : {}));
  },
  admin: async ({}, use) => {
    const bearer = await optionalAdminAccessToken();
    await use(createAdminClient(bearer ? { bearer } : {}));
  },
  memory: async ({}, use) => {
    await use({});
  },
});
