export {
  createAppI18n,
  getAppLocaleFromInstance,
  setAppLocale,
  detectInitialLocale,
  localeFromI18nLanguage,
  setStoredLocale,
  SUPPORTED_LOCALES,
  type AppLocale,
  type AppTranslationResources,
} from "./createAppI18n";
export { THEME_STORAGE_KEY, type AppTheme, DEFAULT_THEME, getAppTheme, isAppTheme, setAppTheme, applyStoredTheme, THEMES } from "../preferences";
