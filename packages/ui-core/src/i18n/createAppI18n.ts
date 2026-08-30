import i18n, { type i18n as I18nInstance } from "i18next";
import { initReactI18next } from "react-i18next";
import adminDe from "@locales/admin/de.json";
import adminEn from "@locales/admin/en.json";
import adminHu from "@locales/admin/hu.json";
import appDe from "@locales/app/de.json";
import appEn from "@locales/app/en.json";
import appHu from "@locales/app/hu.json";
import coreDe from "@locales/core/de.json";
import coreEn from "@locales/core/en.json";
import coreHu from "@locales/core/hu.json";
import messagesDe from "@locales/messages/de.json";
import messagesEn from "@locales/messages/en.json";
import messagesHu from "@locales/messages/hu.json";
import { detectInitialLocale, setStoredLocale, type AppLocale } from "./locale";

export type AppTranslationResources = Record<
  AppLocale,
  { translation: Record<string, unknown> }
>;

export type LocaleNamespace = "app" | "admin";

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

const messagesByLocale: Record<AppLocale, Record<string, unknown>> = {
  en: messagesEn as Record<string, unknown>,
  hu: messagesHu as Record<string, unknown>,
  de: messagesDe as Record<string, unknown>,
};

const coreByLocale: Record<AppLocale, Record<string, unknown>> = {
  en: coreEn as Record<string, unknown>,
  hu: coreHu as Record<string, unknown>,
  de: coreDe as Record<string, unknown>,
};

const appByLocale: Record<AppLocale, Record<string, unknown>> = {
  en: appEn as Record<string, unknown>,
  hu: appHu as Record<string, unknown>,
  de: appDe as Record<string, unknown>,
};

const adminByLocale: Record<AppLocale, Record<string, unknown>> = {
  en: adminEn as Record<string, unknown>,
  hu: adminHu as Record<string, unknown>,
  de: adminDe as Record<string, unknown>,
};

function namespaceByLocale(ns: LocaleNamespace): Record<AppLocale, Record<string, unknown>> {
  return ns === "admin" ? adminByLocale : appByLocale;
}

/** Merge server messages + UI core + one app namespace (app | admin). */
export function buildLocaleResources(ns: LocaleNamespace): AppTranslationResources {
  const appNs = namespaceByLocale(ns);
  return {
    en: {
      translation: mergeDeep(
        mergeDeep(messagesByLocale.en, coreByLocale.en),
        appNs.en,
      ),
    },
    hu: {
      translation: mergeDeep(
        mergeDeep(messagesByLocale.hu, coreByLocale.hu),
        appNs.hu,
      ),
    },
    de: {
      translation: mergeDeep(
        mergeDeep(messagesByLocale.de, coreByLocale.de),
        appNs.de,
      ),
    },
  };
}

export async function createAppI18n(
  appResources: AppTranslationResources,
): Promise<I18nInstance> {
  const instance = i18n.createInstance();
  await instance.use(initReactI18next).init({
    resources: appResources,
    lng: detectInitialLocale(),
    fallbackLng: "en",
    interpolation: { escapeValue: false },
    react: { useSuspense: false },
  });
  return instance;
}

/** Preferred entry: load merged catalogs for ``app`` or ``admin`` from root ``locales/``. */
export async function createAppI18nForNamespace(
  ns: LocaleNamespace,
): Promise<I18nInstance> {
  return createAppI18n(buildLocaleResources(ns));
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
