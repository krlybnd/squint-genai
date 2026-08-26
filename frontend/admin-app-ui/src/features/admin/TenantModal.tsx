import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Modal } from "@are/ui-core";
import { createTenant, deleteTenant, updateTenant, type Tenant } from "../../api/admin";
import { TenantMembersSection } from "./TenantMembersSection";
import { AdminFormField, AdminFormGrid, AdminFormSection } from "./AdminFormLayout";
import "./AdminForm.css";

export type TenantModalMode = { kind: "create" } | { kind: "edit"; tenant: Tenant };

type TenantModalProps = {
  open: boolean;
  mode: TenantModalMode | null;
  onClose: () => void;
  onSaved: () => void;
  onMembershipChanged?: (username?: string) => void;
};

export function TenantModal({ open, mode, onClose, onSaved, onMembershipChanged }: TenantModalProps) {
  const { t } = useTranslation();
  const isEdit = mode?.kind === "edit";
  const [alias, setAlias] = useState("");
  const [name, setName] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open || !mode) return;
    if (mode.kind === "edit") {
      setAlias(mode.tenant.alias);
      setName(mode.tenant.name);
      setEnabled(mode.tenant.enabled);
    } else {
      setAlias("");
      setName("");
      setEnabled(true);
    }
    setError(null);
  }, [open, mode]);

  if (!mode) return null;

  const title = isEdit ? t("admin.editTenant") : t("admin.createTenant");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      if (isEdit && mode?.kind === "edit") {
        await updateTenant(mode.tenant.alias, { name: name.trim(), enabled });
      } else {
        await createTenant(alias.trim(), name.trim());
      }
      onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!isEdit || mode?.kind !== "edit") return;
    if (!window.confirm(t("admin.confirmDeleteTenant", { alias: mode.tenant.alias }))) return;
    setSaving(true);
    setError(null);
    try {
      await deleteTenant(mode.tenant.alias);
      onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  const footer = (
    <>
      {isEdit ? (
        <button type="button" className="ui-btn danger" disabled={saving} onClick={() => void handleDelete()}>
          {t("admin.delete")}
        </button>
      ) : (
        <span />
      )}
      <div className="admin-form-footer-actions">
        <button type="button" className="ui-btn" onClick={onClose} disabled={saving}>
          {t("admin.cancel")}
        </button>
        <button type="submit" form="tenant-modal-form" className="ui-btn primary" disabled={saving}>
          {t("admin.save")}
        </button>
      </div>
    </>
  );

  return (
    <Modal open={open} title={title} onClose={onClose} footer={footer} size={isEdit ? "xl" : "md"}>
      <form id="tenant-modal-form" className="admin-form" onSubmit={(e) => void handleSubmit(e)}>
        {error && (
          <div className="ui-form-error" role="alert">
            {error}
          </div>
        )}
        <AdminFormSection title={t("admin.sectionIdentity")} description={t("admin.sectionIdentityDesc")}>
          <AdminFormGrid>
            <AdminFormField
              id="tenant-alias"
              label={t("admin.tenantAlias")}
              readOnlyValue={isEdit ? alias : undefined}
            >
              {!isEdit && (
                <input
                  id="tenant-alias"
                  type="text"
                  value={alias}
                  onChange={(e) => setAlias(e.target.value)}
                  pattern="^[a-zA-Z0-9_-]+$"
                  required
                />
              )}
            </AdminFormField>
            <AdminFormField id="tenant-name" label={t("admin.tenantName")}>
              <input
                id="tenant-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
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
        {isEdit && mode.kind === "edit" && (
          <AdminFormSection title={t("admin.members")} description={t("admin.sectionMembersDesc")}>
            <TenantMembersSection
              tenantAlias={mode.tenant.alias}
              onMembershipChanged={onMembershipChanged ?? onSaved}
            />
          </AdminFormSection>
        )}
      </form>
    </Modal>
  );
}
