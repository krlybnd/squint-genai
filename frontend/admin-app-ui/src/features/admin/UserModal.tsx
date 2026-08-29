import { FormEvent, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Modal, Select } from "@are/ui-core";
import {
  assignUserTenant,
  createUser,
  updateUser,
  type Tenant,
  type User,
} from "../../api/admin";
import { AdminFormField, AdminFormGrid, AdminFormSection } from "./AdminFormLayout";
import { UserTenantMembershipSection } from "./UserTenantMembershipSection";
import "./AdminForm.css";

export type UserModalMode = { kind: "create" } | { kind: "edit"; user: User };

type UserModalProps = {
  open: boolean;
  mode: UserModalMode | null;
  tenants: Tenant[];
  onClose: () => void;
  onSaved: (user?: User) => void | Promise<void>;
};

export function UserModal({ open, mode, tenants, onClose, onSaved }: UserModalProps) {
  const { t } = useTranslation();
  const isEdit = mode?.kind === "edit";
  const editUsername = mode?.kind === "edit" ? mode.user.username : null;
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [tenantIds, setTenantIds] = useState<string[]>([]);
  const [tenantRoles, setTenantRoles] = useState<Record<string, string[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [createTenantId, setCreateTenantId] = useState("");

  // Reset form when opening or switching user — not on every parent list refresh.
  useEffect(() => {
    if (!open || !mode) return;
    if (mode.kind === "edit") {
      const u = mode.user;
      setUsername(u.username);
      setEmail(u.email ?? "");
      setPassword("");
      setEnabled(u.enabled);
      setTenantId(u.tenant_id);
      setTenantIds(u.tenant_ids ?? []);
      setTenantRoles(u.tenant_roles ?? {});
    } else {
      setUsername("");
      setEmail("");
      setPassword("");
      setEnabled(true);
      setTenantId(null);
      setTenantIds([]);
      setTenantRoles({});
      setCreateTenantId("");
    }
    setError(null);
  }, [open, editUsername, mode?.kind]);

  const tenantOptions = useMemo(
    () =>
      tenants.map((tenant) => ({
        value: tenant.alias,
        label: `${tenant.alias} — ${tenant.name}`,
      })),
    [tenants],
  );

  const createTenantOptions = useMemo(
    () => [{ value: "", label: t("admin.noTenant") }, ...tenantOptions],
    [tenantOptions, t],
  );

  if (!mode) return null;

  const title = isEdit ? t("admin.editUser") : t("admin.createUser");

  function syncFromUser(user: User) {
    setTenantId(user.tenant_id);
    setTenantIds(user.tenant_ids ?? []);
    setTenantRoles(user.tenant_roles ?? {});
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      let savedUser: User | undefined;
      if (isEdit && mode?.kind === "edit") {
        savedUser = await updateUser(mode.user.username, {
          email: email.trim() || null,
          enabled,
          password: password.trim() || undefined,
        });
      } else {
        savedUser = await createUser({
          username: username.trim(),
          email: email.trim() || undefined,
          password,
          realm_roles: [],
        });
        if (createTenantId.trim()) {
          savedUser = await assignUserTenant(username.trim(), createTenantId.trim(), {
            setActive: true,
            roles: ["read"],
          });
        }
      }
      await onSaved(savedUser);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  const footer = (
    <div className="admin-form-footer-actions" style={{ marginLeft: "auto" }}>
      <button type="button" className="ui-btn" onClick={onClose} disabled={saving}>
        {t("admin.cancel")}
      </button>
      <button type="submit" form="user-modal-form" className="ui-btn primary" disabled={saving}>
        {t("admin.save")}
      </button>
    </div>
  );

  return (
    <Modal open={open} title={title} onClose={onClose} footer={footer} size="xl">
      <form id="user-modal-form" className="admin-form" onSubmit={(e) => void handleSubmit(e)}>
        {error && (
          <div className="ui-form-error" role="alert">
            {error}
          </div>
        )}

        <AdminFormSection title={t("admin.sectionAccount")} description={t("admin.sectionAccountDesc")}>
          <AdminFormGrid>
            <AdminFormField
              id="user-username"
              label={t("admin.username")}
              readOnlyValue={isEdit ? username : undefined}
            >
              {!isEdit && (
                <input
                  id="user-username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              )}
            </AdminFormField>
            <AdminFormField id="user-email" label={t("admin.email")}>
              <input
                id="user-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </AdminFormField>
            <AdminFormField
              id="user-password"
              label={isEdit ? t("admin.newPasswordOptional") : t("admin.password")}
              span={2}
            >
              <input
                id="user-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required={!isEdit}
                minLength={isEdit ? undefined : 4}
              />
            </AdminFormField>
          </AdminFormGrid>
          {isEdit && (
            <label className="admin-form-inline-check ui-checkbox">
              <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
              {t("admin.enabled")}
            </label>
          )}
        </AdminFormSection>

        <AdminFormSection title={t("admin.sectionTenants")} description={t("admin.sectionTenantsDesc")}>
          {isEdit && mode.kind === "edit" ? (
            <UserTenantMembershipSection
              username={mode.user.username}
              tenantId={tenantId}
              tenantIds={tenantIds}
              tenantRoles={tenantRoles}
              tenants={tenants}
              disabled={saving}
              onUpdated={async (user) => {
                syncFromUser(user);
                await onSaved(user);
              }}
              onError={setError}
            />
          ) : (
            <AdminFormField id="user-create-tenant" label={t("admin.assignTenant")} span={2}>
              <Select
                value={createTenantId}
                options={createTenantOptions}
                onChange={setCreateTenantId}
                ariaLabel={t("admin.tenantLabel")}
                placeholder={t("admin.noTenant")}
              />
            </AdminFormField>
          )}
        </AdminFormSection>
      </form>
    </Modal>
  );
}
