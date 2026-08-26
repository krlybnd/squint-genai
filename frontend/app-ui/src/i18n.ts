import type { i18n as I18nInstance } from "i18next";
import { createAppI18nFromLocales } from "@are/ui-core/app/appI18n";
import de from "./locales/de.json";
import en from "./locales/en.json";
import hu from "./locales/hu.json";

let instance: I18nInstance | undefined;

export async function initAppI18n(): Promise<I18nInstance> {
  instance = await createAppI18nFromLocales({ en, hu, de });
  return instance;
}

export function getAppI18n(): I18nInstance {
  if (!instance) {
    throw new Error("i18n is not initialized — call initAppI18n() first");
  }
  return instance;
}
