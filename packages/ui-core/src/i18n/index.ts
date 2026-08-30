export {
  createAppI18n,
  createAppI18nForNamespace,
  buildLocaleResources,
  getAppLocaleFromInstance,
  setAppLocale,
  detectInitialLocale,
  localeFromI18nLanguage,
  setStoredLocale,
  SUPPORTED_LOCALES,
  type AppLocale,
  type AppTranslationResources,
  type LocaleNamespace,
} from "./createAppI18n";
export { THEME_STORAGE_KEY, type AppTheme, DEFAULT_THEME, getAppTheme, isAppTheme, setAppTheme, applyStoredTheme, THEMES } from "../preferences";
