import type { i18n as I18nInstance } from "i18next";
import {
  buildLocaleResources,
  createAppI18n,
  createAppI18nForNamespace,
  type AppTranslationResources,
  type LocaleNamespace,
} from "../i18n";

function mergeDeep(
  base: Record<string, unknown>,
  overlay: Record<string, unknown>,
): Record<string, unknown> {
  const out = { ...base };
  for (const [key, value] of Object.entries(overlay)) {
    if (value && typeof value === "object" && !Array.isArray(value)) {
      out[key] = mergeDeep(
        (base[key] as Record<string, unknown> | undefined) ?? {},
        value as Record<string, unknown>,
      );
    } else {
      out[key] = value;
    }
  }
  return out;
}

/** @deprecated Prefer ``initI18n("app" | "admin")`` — root ``locales/`` namespaces. */
export async function createAppI18nFromLocales(
  locales: Record<"en" | "hu" | "de", Record<string, unknown>>,
): Promise<I18nInstance> {
  const base = buildLocaleResources("app");
  const appResources = {
    en: { translation: mergeDeep(base.en.translation, locales.en) },
    hu: { translation: mergeDeep(base.hu.translation, locales.hu) },
    de: { translation: mergeDeep(base.de.translation, locales.de) },
  } satisfies AppTranslationResources;

  return createAppI18n(appResources);
}

export async function initI18n(ns: LocaleNamespace): Promise<I18nInstance> {
  return createAppI18nForNamespace(ns);
}
