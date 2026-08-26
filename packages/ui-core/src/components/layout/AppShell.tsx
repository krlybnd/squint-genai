import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { SquintLogo } from "../icons/SquintLogo";
import { UserProfileMenu, type UserProfileMenuProps } from "../UserProfileMenu";
import "./AppShell.css";

export type AppShellProps = {
  title?: string;
  icon?: ReactNode;
  sidebar: ReactNode;
  children: ReactNode;
  headerEnd?: ReactNode;
  profileMenu?: UserProfileMenuProps;
};

export function AppShell({ title, icon, sidebar, children, headerEnd, profileMenu }: AppShellProps) {
  const { t } = useTranslation();
  const displayTitle = title ?? t("app.title");

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <div className="logo-icon">{icon ?? <SquintLogo size={28} />}</div>
          <div>
            <span className="logo-title">{displayTitle}</span>
          </div>
        </div>
        {headerEnd ? <div className="header-actions">{headerEnd}</div> : null}
      </header>

      <main className="app-main">
        <aside className="sidebar">
          {sidebar}
          <UserProfileMenu {...profileMenu} />
        </aside>
        <section className="app-content">{children}</section>
      </main>
    </div>
  );
}
