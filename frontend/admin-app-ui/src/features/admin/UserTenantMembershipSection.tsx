import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  assignUserTenant,
  removeUserFromTenant,
  setActiveUserTenant,
  setUserTenantRoles,
  type Tenant,
  type User,
} from "../../api/admin";
import { MembershipPanel, type MembershipRow } from "./MembershipPanel";

type UserTenantMembershipSectionProps = {
  username: string;
  tenantId: string | null;
  tenantIds: string[];
  tenantRoles: Record<string, string[]>;
  tenants: Tenant[];
  disabled?: boolean;
  onUpdated: (user: User) => void | Promise<void>;
  onError: (message: string | null) => void;
};

export function UserTenantMembershipSection({
  username,
  tenantId,
  tenantIds,
  tenantRoles,
  tenants,
  disabled = false,
  onUpdated,
  onError,
}: UserTenantMembershipSectionProps) {
  const { t } = useTranslation();
  const [pickTenant, setPickTenant] = useState("");
  const [addRoles, setAddRoles] = useState<string[]>(["read"]);
  const [busy, setBusy] = useState(false);

  const tenantOptions = useMemo(
    () =>
      tenants.map((tenant) => ({
        value: tenant.alias,
        label: `${tenant.alias} — ${tenant.name}`,
      })),
    [tenants],
  );

  const assignTenantOptions = useMemo(
    () => tenantOptions.filter((option) => !tenantIds.includes(option.value)),
    [tenantOptions, tenantIds],
  );

  const tenantNameByAlias = useMemo(
    () => new Map(tenants.map((tenant) => [tenant.alias, tenant.name])),
    [tenants],
  );

  async function runTenantAction(action: () => Promise<User>) {
    setBusy(true);
    onError(null);
    try {
      const updated = await action();
      setPickTenant("");
      setAddRoles(["read"]);
      await onUpdated(updated);
    } catch (err) {
      onError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  function handleAssignTenant() {
    const alias = pickTenant.trim();
    if (!alias) return;
    void runTenantAction(() =>
      assignUserTenant(username, alias, {
        setActive: tenantIds.length === 0,
        roles: addRoles,
      }),
    );
  }

  function handleRemoveTenant(alias: string) {
    if (!window.confirm(t("admin.confirmRemoveUserTenant", { alias }))) return;
    void runTenantAction(() => removeUserFromTenant(username, alias));
  }

  function handleSetActive(alias: string) {
    void runTenantAction(() => setActiveUserTenant(username, alias));
  }

  function handleRolesChange(alias: string, roles: string[]) {
    void runTenantAction(() => setUserTenantRoles(username, alias, roles));
  }

  const items: MembershipRow[] = tenantIds.map((alias) => ({
    id: alias,
    primary: alias,
    secondary: tenantNameByAlias.get(alias),
    badge: tenantId === alias ? t("admin.activeTenant") : undefined,
    roles: tenantRoles[alias] ?? [],
    rolesDisabled: disabled || busy,
    onRolesChange: (roles) => handleRolesChange(alias, roles),
    actions: [
      ...(tenantId !== alias
        ? [
            {
              key: "active",
              label: t("admin.setActiveTenant"),
              disabled: disabled || busy,
              onClick: () => handleSetActive(alias),
            },
          ]
        : []),
      {
        key: "remove",
        label: t("admin.removeMember"),
        variant: "danger" as const,
        disabled: disabled || busy,
        onClick: () => handleRemoveTenant(alias),
      },
    ],
  }));

  return (
    <MembershipPanel
      emptyMessage={t("admin.noTenant")}
      hint={t("admin.multiTenantHint")}
      items={items}
      layout="dual"
      add={{
        value: pickTenant,
        options: [{ value: "", label: t("admin.selectTenant") }, ...assignTenantOptions],
        onChange: setPickTenant,
        placeholder: t("admin.selectTenant"),
        ariaLabel: t("admin.assignTenant"),
        disabled: disabled || busy || assignTenantOptions.length === 0,
        buttonLabel: t("admin.addMember"),
        onAdd: handleAssignTenant,
        addDisabled: disabled || busy || !pickTenant.trim(),
        roles: addRoles,
        onRolesChange: setAddRoles,
        rolesLabel: t("admin.tenantRolesLabel"),
      }}
    />
  );
}
