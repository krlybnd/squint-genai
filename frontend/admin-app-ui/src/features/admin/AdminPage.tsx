import { useCallback, useEffect, useMemo, useState } from "react";
import { Building2, Users } from "lucide-react";
import { useTranslation } from "react-i18next";
import { AppShell } from "@are/ui-core";
import { fetchTenants, fetchUser, fetchUsers, type Tenant, type User } from "../../api/admin";
import { AdminNavPanel, type AdminSectionId } from "./AdminNavPanel";
import { AdminResourcePanel } from "./AdminResourcePanel";
import { TenantModal, type TenantModalMode } from "./TenantModal";
import { UserModal, type UserModalMode } from "./UserModal";
import "./AdminPage.css";

function mergeUserIntoList(list: User[], patch: User): User[] {
  const idx = list.findIndex((u) => u.username === patch.username);
  if (idx < 0) return [...list, patch];
  const next = [...list];
  next[idx] = patch;
  return next;
}

export function AdminPage() {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] = useState<AdminSectionId>("tenants");
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [tenantModal, setTenantModal] = useState<TenantModalMode | null>(null);
  const [userModal, setUserModal] = useState<UserModalMode | null>(null);

  const navItems = useMemo(
    () => [
      { id: "tenants" as const, label: t("admin.tenantsTitle"), icon: Building2 },
      { id: "users" as const, label: t("admin.usersTitle"), icon: Users },
    ],
    [t],
  );

  const applyUserToState = useCallback((user: User) => {
    setUsers((prev) => mergeUserIntoList(prev, user));
    setUserModal((prev) =>
      prev?.kind === "edit" && prev.user.username === user.username
        ? { kind: "edit", user }
        : prev,
    );
  }, []);

  const refreshLists = useCallback(async (userPatch?: User) => {
    const [tList, uList] = await Promise.all([fetchTenants(), fetchUsers()]);
    const mergedUsers = userPatch ? mergeUserIntoList(uList, userPatch) : uList;

      setTenants(tList);
      setUsers(mergedUsers);
      setUserModal((prev) => {
        if (prev?.kind !== "edit") return prev;
        const fresh = mergedUsers.find((u) => u.username === prev.user.username);
        return fresh ? { kind: "edit", user: fresh } : prev;
      });
      setTenantModal((prev) => {
        if (prev?.kind !== "edit") return prev;
        const fresh = tList.find((tenant) => tenant.alias === prev.tenant.alias);
        return fresh ? { kind: "edit", tenant: fresh } : prev;
      });
  }, []);

  const handleUserSaved = useCallback(
    async (user?: User) => {
      if (user) {
        applyUserToState(user);
      }
      try {
        await refreshLists(user);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    },
    [applyUserToState, refreshLists],
  );

  const handleTenantMembershipChanged = useCallback(
    async (username?: string) => {
      if (username) {
        try {
          const user = await fetchUser(username);
          await handleUserSaved(user);
          return;
        } catch {
          /* fall through to full refresh */
        }
      }
      try {
        await refreshLists();
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    },
    [handleUserSaved, refreshLists],
  );

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await refreshLists();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [refreshLists]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return (
    <>
      <AppShell
        sidebar={
          <AdminNavPanel items={navItems} activeId={activeSection} onSelect={setActiveSection} />
        }
      >
        <div className="admin-page admin-workspace">
          {error && (
            <div className="admin-banner-error" role="alert">
              {error}
            </div>
          )}
          {activeSection === "tenants" ? (
            <AdminResourcePanel<Tenant>
              title={t("admin.tenantsTitle")}
              hint={t("admin.doubleClickEdit")}
              emptyMessage={loading ? t("admin.loading") : t("admin.noTenants")}
              createLabel={t("admin.newTenant")}
              loading={loading}
              items={tenants}
              itemKey={(item) => item.id}
              onCreate={() => setTenantModal({ kind: "create" })}
              onEdit={(item) => setTenantModal({ kind: "edit", tenant: item })}
              renderPrimary={(item) => (
                <>
                  <strong>{item.alias}</strong>
                  <span className="admin-resource-muted"> — {item.name}</span>
                  {!item.enabled && (
                    <span className="ui-badge">{t("admin.disabled")}</span>
                  )}
                </>
              )}
            />
          ) : (
            <AdminResourcePanel<User>
              title={t("admin.usersTitle")}
              hint={t("admin.doubleClickEdit")}
              emptyMessage={loading ? t("admin.loading") : t("admin.noUsers")}
              createLabel={t("admin.newUser")}
              loading={loading}
              items={users}
              itemKey={(item) => item.id}
              onCreate={() => setUserModal({ kind: "create" })}
              onEdit={(item) => setUserModal({ kind: "edit", user: item })}
              renderPrimary={(item) => (
                <>
                  <strong>{item.username}</strong>
                  {item.email && <span className="admin-resource-muted"> ({item.email})</span>}
                </>
              )}
              renderMeta={(item) => (
                <>
                  {t("admin.tenantLabel")}:{" "}
                  {item.tenant_ids.length
                    ? item.tenant_ids
                        .map((id) => (id === item.tenant_id ? `${id} (${t("admin.activeTenant")})` : id))
                        .join(", ")
                    : "—"}{" "}
                  · {t("admin.rolesLabel")}: {item.realm_roles.join(", ") || "—"}
                </>
              )}
            />
          )}
        </div>
      </AppShell>

      <TenantModal
        open={tenantModal !== null}
        mode={tenantModal}
        onClose={() => setTenantModal(null)}
        onSaved={() => void refreshLists()}
        onMembershipChanged={(username) => void handleTenantMembershipChanged(username)}
      />
      <UserModal
        open={userModal !== null}
        mode={userModal}
        tenants={tenants}
        onClose={() => setUserModal(null)}
        onSaved={handleUserSaved}
      />
    </>
  );
}
