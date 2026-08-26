import { DEFAULT_THEME, isAppTheme, type AppTheme } from "./themes";

export const THEME_STORAGE_KEY = "app-theme";
export { DEFAULT_THEME, isAppTheme, type AppTheme } from "./themes";

export function getAppTheme(): AppTheme {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  return isAppTheme(stored) ? stored : DEFAULT_THEME;
}

export function setAppTheme(theme: AppTheme): void {
  localStorage.setItem(THEME_STORAGE_KEY, theme);
  document.documentElement.setAttribute("data-theme", theme);
}

export function applyStoredTheme(): void {
  document.documentElement.setAttribute("data-theme", getAppTheme());
}
