export const LOCALE_STORAGE_KEY = "app-locale";
export const THEME_STORAGE_KEY = "app-theme";
export const SUPPORTED_LOCALES = ["en", "hu", "de"] as const;
export type AppLocale = (typeof SUPPORTED_LOCALES)[number];
export type AppTheme = "purple" | "neptune";

export function detectInitialLocale(): AppLocale {
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY);
  if (stored && SUPPORTED_LOCALES.includes(stored as AppLocale)) {
    return stored as AppLocale;
  }
  const browser = navigator.language.split("-")[0];
  if (SUPPORTED_LOCALES.includes(browser as AppLocale)) {
    return browser as AppLocale;
  }
  return "en";
}

export function localeFromI18nLanguage(language: string): AppLocale {
  const lang = language.split("-")[0];
  return SUPPORTED_LOCALES.includes(lang as AppLocale) ? (lang as AppLocale) : "en";
}

export function setStoredLocale(locale: AppLocale): void {
  localStorage.setItem(LOCALE_STORAGE_KEY, locale);
}
