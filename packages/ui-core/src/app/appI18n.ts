import type { AppTranslationResources } from "../i18n";
import { createAppI18n } from "../i18n";

export function createAppI18nFromLocales(
  locales: Record<"en" | "hu" | "de", Record<string, unknown>>,
) {
  const appResources = {
    en: { translation: locales.en },
    hu: { translation: locales.hu },
    de: { translation: locales.de },
  } satisfies AppTranslationResources;

  return createAppI18n(appResources);
}
