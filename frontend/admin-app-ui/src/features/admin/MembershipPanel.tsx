import { Select, type SelectOption } from "@are/ui-core";
import { APP_ROLES } from "../../api/admin";
import "./AdminForm.css";

export type MembershipRowAction = {
  key: string;
  label: string;
  variant?: "default" | "danger";
  onClick: () => void;
  disabled?: boolean;
};

export type MembershipRow = {
  id: string;
  primary: string;
  secondary?: string;
  badge?: string;
  roles?: string[];
  onRolesChange?: (roles: string[]) => void;
  rolesDisabled?: boolean;
  actions: MembershipRowAction[];
};

export type MembershipPanelSearch = {
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

export type MembershipPanelAdd = {
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  placeholder: string;
  ariaLabel: string;
  disabled?: boolean;
  buttonLabel: string;
  onAdd: () => void;
  addDisabled?: boolean;
};

export type MembershipPanelLoadMore = {
  key: string;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  loadingLabel?: string;
  placement?: "before-list" | "after-list";
};

export type MembershipPanelProps = {
  error?: string | null;
  loading?: boolean;
  loadingMessage?: string;
  emptyMessage: string;
  hint?: string;
  items: MembershipRow[];
  layout?: "dual" | "compact";
  search?: MembershipPanelSearch;
  add: MembershipPanelAdd;
  loadMore?: MembershipPanelLoadMore[];
  className?: string;
};

function toggleRole(roles: string[], role: string): string[] {
  return roles.includes(role) ? roles.filter((r) => r !== role) : [...roles, role];
}

function RoleCheckboxes({
  roles,
  onChange,
  disabled,
}: {
  roles: string[];
  onChange: (roles: string[]) => void;
  disabled?: boolean;
}) {
  return (
    <div className="admin-membership-roles">
      <div className="admin-form-roles">
        {APP_ROLES.map((role) => (
          <label key={role} className="ui-checkbox">
            <input
              type="checkbox"
              checked={roles.includes(role)}
              disabled={disabled}
              onChange={(e) => {
                e.stopPropagation();
                onChange(toggleRole(roles, role));
              }}
            />
            {role}
          </label>
        ))}
      </div>
    </div>
  );
}

function LoadMoreButton({ entry }: { entry: MembershipPanelLoadMore }) {
  return (
    <button
      type="button"
      className="ui-btn admin-members-load-more"
      disabled={entry.disabled}
      onClick={() => entry.onClick()}
    >
      {entry.loading ? (entry.loadingLabel ?? entry.label) : entry.label}
    </button>
  );
}

export function MembershipPanel({
  error,
  loading = false,
  loadingMessage,
  emptyMessage,
  hint,
  items,
  layout = "compact",
  search,
  add,
  loadMore = [],
  className,
}: MembershipPanelProps) {
  const loadMoreBefore = loadMore.filter((entry) => (entry.placement ?? "before-list") === "before-list");
  const loadMoreAfter = loadMore.filter((entry) => entry.placement === "after-list");

  return (
    <div className={className ? `admin-membership-panel ${className}` : "admin-membership-panel"}>
      {error ? (
        <div className="ui-form-error" role="alert">
          {error}
        </div>
      ) : null}

      {search ? (
        <label className="admin-form-field">
          <span className="admin-form-field-label">{search.label}</span>
          <input
            type="search"
            value={search.value}
            onChange={(e) => search.onChange(e.target.value)}
            placeholder={search.placeholder}
            disabled={search.disabled}
          />
        </label>
      ) : null}

      <div className="admin-members-add">
        <Select
          value={add.value}
          options={add.options}
          onChange={add.onChange}
          ariaLabel={add.ariaLabel}
          disabled={add.disabled}
          placeholder={add.placeholder}
        />
        <button
          type="button"
          className="ui-btn primary"
          disabled={add.addDisabled}
          onClick={() => add.onAdd()}
        >
          {add.buttonLabel}
        </button>
      </div>

      {loadMoreBefore.map((entry) => (
        <LoadMoreButton key={entry.key} entry={entry} />
      ))}

      {loading ? (
        <p className="admin-members-hint">{loadingMessage ?? emptyMessage}</p>
      ) : items.length === 0 ? (
        <p className="admin-members-hint">{emptyMessage}</p>
      ) : (
        <ul className="admin-members-list">
          {items.map((item) => (
            <li
              key={item.id}
              className={`admin-membership-row${layout === "dual" ? " dual" : " compact"}${
                item.onRolesChange ? " with-roles" : ""
              }`}
            >
              {layout === "dual" ? (
                <>
                  <span className="admin-membership-primary">{item.primary}</span>
                  <span className="admin-membership-secondary">{item.secondary ?? "—"}</span>
                </>
              ) : (
                <span className="admin-membership-primary">
                  <strong>{item.primary}</strong>
                  {item.secondary ? (
                    <span className="admin-form-muted"> ({item.secondary})</span>
                  ) : null}
                </span>
              )}
              <span className="admin-membership-actions">
                {item.actions.map((action) => (
                  <button
                    key={action.key}
                    type="button"
                    className={`ui-btn${action.variant === "danger" ? " danger admin-membership-action-remove" : ""}`}
                    disabled={action.disabled}
                    onClick={() => action.onClick()}
                  >
                    {action.label}
                  </button>
                ))}
              </span>
              {item.badge ? (
                <span className="admin-membership-meta">
                  <span className="ui-badge">{item.badge}</span>
                </span>
              ) : null}
              {item.onRolesChange ? (
                <div className="admin-membership-row-roles">
                  <RoleCheckboxes
                    roles={item.roles ?? []}
                    onChange={item.onRolesChange}
                    disabled={item.rolesDisabled}
                  />
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      )}

      {loadMoreAfter.map((entry) => (
        <LoadMoreButton key={entry.key} entry={entry} />
      ))}

      {hint ? <p className="admin-members-hint">{hint}</p> : null}
    </div>
  );
}
