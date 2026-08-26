export const THEMES = [
  { id: "purple", labelKey: "theme.purple" },
  { id: "neptune", labelKey: "theme.neptune" },
] as const;

export type AppTheme = (typeof THEMES)[number]["id"];

export const DEFAULT_THEME: AppTheme = "purple";

export function isAppTheme(value: unknown): value is AppTheme {
  return typeof value === "string" && THEMES.some((theme) => theme.id === value);
}
