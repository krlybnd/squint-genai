import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronUp, LogOut, Shield } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useAuth } from "../auth/AuthProvider";
import { SUPPORTED_LOCALES } from "../i18n/locale";
import { THEMES } from "../preferences/themes";
import { usePreferences } from "../preferences/PreferencesProvider";
import "./UserProfileMenu.css";

export type UserProfileMenuProps = {
  adminPanelHref?: string;
};

function initialsFromUsername(username: string | null): string {
  const name = (username ?? "user").trim();
  if (!name) return "?";
  const parts = name.split(/[@.\s_-]+/).filter(Boolean);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

export function UserProfileMenu({ adminPanelHref }: UserProfileMenuProps = {}) {
  const { t } = useTranslation();
  const auth = useAuth();
  const { locale, theme, setLocale, setTheme } = usePreferences();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const initials = useMemo(() => initialsFromUsername(auth.username), [auth.username]);
  const displayName = auth.username ?? t("prefs.guest");

  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const showAdminLink =
    adminPanelHref && (!auth.client.enabled || auth.hasAnyRole("admin"));

  return (
    <div className={`profile-menu${open ? " open" : ""}`} ref={rootRef}>
      {open && (
        <div className="profile-menu-dropdown" role="menu" aria-label={t("prefs.accountMenu")}>
          <div className="profile-menu-section">
            <span className="profile-menu-section-label">{t("prefs.language")}</span>
            <div className="profile-menu-options" role="group" aria-label={t("prefs.language")}>
              {SUPPORTED_LOCALES.map((code) => (
                <button
                  key={code}
                  type="button"
                  role="menuitemradio"
                  aria-checked={locale === code}
                  className={`profile-menu-option${locale === code ? " active" : ""}`}
                  onClick={() => setLocale(code)}
                >
                  {t(`lang.${code}`)}
                </button>
              ))}
            </div>
          </div>
          <div className="profile-menu-section">
            <span className="profile-menu-section-label">{t("prefs.theme")}</span>
            <div className="profile-menu-options" role="group" aria-label={t("prefs.theme")}>
              {THEMES.map((entry) => (
                <button
                  key={entry.id}
                  type="button"
                  role="menuitemradio"
                  aria-checked={theme === entry.id}
                  className={`profile-menu-option${theme === entry.id ? " active" : ""}`}
                  onClick={() => setTheme(entry.id)}
                >
                  {t(entry.labelKey)}
                </button>
              ))}
            </div>
          </div>
          {showAdminLink && (
            <>
              <div className="profile-menu-divider" />
              <a
                href={adminPanelHref}
                role="menuitem"
                className="profile-menu-logout"
                onClick={() => setOpen(false)}
              >
                <Shield size={16} />
                {t("admin.panelLink")}
              </a>
            </>
          )}
          {auth.client.enabled && (
            <>
              <div className="profile-menu-divider" />
              <button
                type="button"
                role="menuitem"
                className="profile-menu-logout"
                onClick={() => {
                  setOpen(false);
                  auth.logout();
                }}
              >
                <LogOut size={16} />
                {t("prefs.logout")}
              </button>
            </>
          )}
        </div>
      )}
      <button
        type="button"
        className="profile-menu-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((prev) => !prev)}
      >
        <span className="profile-menu-avatar" aria-hidden>
          {initials}
        </span>
        <span className="profile-menu-name">{displayName}</span>
        <ChevronUp size={16} className="profile-menu-chevron" aria-hidden />
      </button>
    </div>
  );
}
