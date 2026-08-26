import type { ReactNode } from "react";
import { Plus } from "lucide-react";
import "./AdminResourcePanel.css";

export type AdminResourcePanelProps<T> = {
  title: string;
  hint: string;
  emptyMessage: string;
  createLabel: string;
  loading?: boolean;
  items: T[];
  itemKey: (item: T) => string;
  onCreate: () => void;
  onEdit: (item: T) => void;
  renderPrimary: (item: T) => ReactNode;
  renderMeta?: (item: T) => ReactNode;
};

export function AdminResourcePanel<T>({
  title,
  hint,
  emptyMessage,
  createLabel,
  loading,
  items,
  itemKey,
  onCreate,
  onEdit,
  renderPrimary,
  renderMeta,
}: AdminResourcePanelProps<T>) {
  return (
    <section className="admin-resource-panel">
      <header className="admin-resource-header">
        <div className="admin-resource-header-text">
          <h2>{title}</h2>
          <span className="admin-resource-hint">{hint}</span>
        </div>
        <button type="button" className="admin-resource-create" onClick={onCreate}>
          <Plus size={16} />
          {createLabel}
        </button>
      </header>

      <ul className="admin-resource-list">
        {loading ? (
          <li className="admin-resource-empty">{emptyMessage}</li>
        ) : items.length === 0 ? (
          <li className="admin-resource-empty">{emptyMessage}</li>
        ) : (
          items.map((item) => (
            <li
              key={itemKey(item)}
              className="admin-resource-row"
              onDoubleClick={() => onEdit(item)}
            >
              <div className="admin-resource-row-main">{renderPrimary(item)}</div>
              {renderMeta ? <div className="admin-resource-row-meta">{renderMeta(item)}</div> : null}
            </li>
          ))
        )}
      </ul>
    </section>
  );
}
