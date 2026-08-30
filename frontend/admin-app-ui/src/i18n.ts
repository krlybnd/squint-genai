import type { i18n as I18nInstance } from "i18next";
import { initI18n } from "@are/ui-core/app/appI18n";

let instance: I18nInstance | undefined;

export async function initAppI18n(): Promise<I18nInstance> {
  instance = await initI18n("admin");
  return instance;
}

export function getAppI18n(): I18nInstance {
  if (!instance) {
    throw new Error("i18n is not initialized — call initAppI18n() first");
  }
  return instance;
}
