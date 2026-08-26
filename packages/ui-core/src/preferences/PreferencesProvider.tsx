import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { i18n as I18nInstance } from "i18next";
import { getAppLocaleFromInstance, setAppLocale, type AppLocale } from "../i18n/createAppI18n";
import { applyStoredTheme, getAppTheme, setAppTheme, type AppTheme } from "./theme";

interface PreferencesContextValue {
  locale: AppLocale;
  theme: AppTheme;
  setLocale: (locale: AppLocale) => void;
  setTheme: (theme: AppTheme) => void;
}

const PreferencesContext = createContext<PreferencesContextValue | null>(null);

export function PreferencesProvider({
  i18n,
  children,
}: {
  i18n: I18nInstance;
  children: ReactNode;
}) {
  const [locale, setLocaleState] = useState<AppLocale>(() => getAppLocaleFromInstance(i18n));
  const [theme, setThemeState] = useState<AppTheme>(() => {
    applyStoredTheme();
    return getAppTheme();
  });

  const value = useMemo(
    () => ({
      locale,
      theme,
      setLocale: (next: AppLocale) => {
        void setAppLocale(i18n, next);
        setLocaleState(next);
      },
      setTheme: (next: AppTheme) => {
        setAppTheme(next);
        setThemeState(next);
      },
    }),
    [i18n, locale, theme],
  );

  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>;
}

export function usePreferences(): PreferencesContextValue {
  const ctx = useContext(PreferencesContext);
  if (!ctx) throw new Error("usePreferences must be used within PreferencesProvider");
  return ctx;
}
