import type { LucideIcon } from "lucide-react";
import { Home, Shield } from "lucide-react";
import { useTranslation } from "react-i18next";
import "./AdminNavPanel.css";

export type AdminSectionId = "tenants" | "users";

export type AdminNavItem = {
  id: AdminSectionId;
  label: string;
  icon: LucideIcon;
};

type AdminNavPanelProps = {
  items: AdminNavItem[];
  activeId: AdminSectionId;
  onSelect: (id: AdminSectionId) => void;
};

export function AdminNavPanel({ items, activeId, onSelect }: AdminNavPanelProps) {
  const { t } = useTranslation();

  return (
    <div className="admin-nav-panel">
      <div className="admin-nav-head">
        <Shield size={18} aria-hidden />
        <span>{t("admin.navTitle")}</span>
      </div>
      <a href="/" className="admin-nav-home">
        <Home size={16} />
        {t("admin.backToApp")}
      </a>
      <nav className="admin-nav-menu" aria-label={t("admin.navTitle")}>
        {items.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            className={`admin-nav-item${activeId === id ? " active" : ""}`}
            aria-current={activeId === id ? "page" : undefined}
            onClick={() => onSelect(id)}
          >
            <Icon size={16} aria-hidden />
            {label}
          </button>
        ))}
      </nav>
    </div>
  );
}
