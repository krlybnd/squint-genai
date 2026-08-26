import i18n, { type i18n as I18nInstance } from "i18next";
import { initReactI18next } from "react-i18next";
import backendDe from "../../../shared/src/agentic_shared/locales/messages/de.json";
import backendEn from "../../../shared/src/agentic_shared/locales/messages/en.json";
import backendHu from "../../../shared/src/agentic_shared/locales/messages/hu.json";
import coreDe from "./locales/core/de.json";
import coreEn from "./locales/core/en.json";
import coreHu from "./locales/core/hu.json";
import { detectInitialLocale, setStoredLocale, type AppLocale } from "./locale";

export type AppTranslationResources = Record<
  AppLocale,
  { translation: Record<string, unknown> }
>;

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

const coreResources: AppTranslationResources = {
  en: {
    translation: mergeDeep(
      backendEn as Record<string, unknown>,
      coreEn as Record<string, unknown>,
    ),
  },
  hu: {
    translation: mergeDeep(
      backendHu as Record<string, unknown>,
      coreHu as Record<string, unknown>,
    ),
  },
  de: {
    translation: mergeDeep(
      backendDe as Record<string, unknown>,
      coreDe as Record<string, unknown>,
    ),
  },
};

export async function createAppI18n(appResources: AppTranslationResources): Promise<I18nInstance> {
  const resources: AppTranslationResources = {
    en: { translation: mergeDeep(coreResources.en.translation, appResources.en?.translation ?? {}) },
    hu: { translation: mergeDeep(coreResources.hu.translation, appResources.hu?.translation ?? {}) },
    de: { translation: mergeDeep(coreResources.de.translation, appResources.de?.translation ?? {}) },
  };

  const instance = i18n.createInstance();
  await instance.use(initReactI18next).init({
    resources,
    lng: detectInitialLocale(),
    fallbackLng: "en",
    interpolation: { escapeValue: false },
    react: { useSuspense: false },
  });
  return instance;
}

export function getAppLocaleFromInstance(instance: I18nInstance): AppLocale {
  const lang = instance.language.split("-")[0];
  return lang === "hu" || lang === "de" ? lang : "en";
}

export async function setAppLocale(instance: I18nInstance, locale: AppLocale): Promise<void> {
  setStoredLocale(locale);
  await instance.changeLanguage(locale);
}

export { detectInitialLocale, localeFromI18nLanguage, setStoredLocale, SUPPORTED_LOCALES, type AppLocale } from "./locale";
