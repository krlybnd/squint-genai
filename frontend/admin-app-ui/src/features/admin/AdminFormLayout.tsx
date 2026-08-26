import type { ReactNode } from "react";

type AdminFormSectionProps = {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
};

export function AdminFormSection({ title, description, children, className }: AdminFormSectionProps) {
  return (
    <section className={`admin-form-section${className ? ` ${className}` : ""}`}>
      <header className="admin-form-section-header">
        <h3 className="admin-form-section-title">{title}</h3>
        {description ? <p className="admin-form-section-desc">{description}</p> : null}
      </header>
      <div className="admin-form-section-body">{children}</div>
    </section>
  );
}

type AdminFormGridProps = {
  children: ReactNode;
  columns?: 1 | 2;
};

export function AdminFormGrid({ children, columns = 2 }: AdminFormGridProps) {
  return <div className={`admin-form-grid cols-${columns}`}>{children}</div>;
}

type AdminFormFieldProps = {
  id: string;
  label: string;
  hint?: string;
  span?: 1 | 2;
  readOnlyValue?: string;
  children?: ReactNode;
};

export function AdminFormField({ id, label, hint, span = 1, readOnlyValue, children }: AdminFormFieldProps) {
  const isReadOnly = readOnlyValue !== undefined;

  return (
    <div className={`admin-form-field${span === 2 ? " span-2" : ""}${isReadOnly ? " readonly" : ""}`}>
      <label className="admin-form-field-label" htmlFor={isReadOnly ? undefined : id}>
        {label}
      </label>
      {isReadOnly ? (
        <div className="admin-form-readonly" id={id} aria-readonly="true">
          {readOnlyValue || "—"}
        </div>
      ) : (
        children
      )}
      {hint ? <p className="admin-form-field-hint">{hint}</p> : null}
    </div>
  );
}
