import { test as bddTest } from "playwright-bdd";

import {
  createAdminClient,
  createApiClient,
  createChatClient,
  type AdminClient,
  type ApiClient,
  type ChatClient,
} from "../src/clients";
import type { AdminComponents, ApiComponents, ChatComponents } from "../src/generated";

export { expect } from "@playwright/test";

export type ChatSession = ChatComponents["schemas"]["ChatSessionOut"];
export type DocumentList = ApiComponents["schemas"]["DocumentListResponse"];
export type MeOut = ApiComponents["schemas"]["MeOut"];
export type TenantList = AdminComponents["schemas"]["TenantListResponse"];
export type UserList = AdminComponents["schemas"]["UserListResponse"];

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
};

export const test = bddTest.extend<{
  api: ApiClient;
  chat: ChatClient;
  admin: AdminClient;
  memory: ScenarioMemory;
}>({
  api: async ({}, use) => {
    await use(createApiClient());
  },
  chat: async ({}, use) => {
    await use(createChatClient());
  },
  admin: async ({}, use) => {
    await use(createAdminClient());
  },
  memory: async ({}, use) => {
    await use({});
  },
});
