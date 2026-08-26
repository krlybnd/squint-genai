import { useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import "./Modal.css";

export type ModalSize = "sm" | "md" | "lg" | "xl" | "full";

export type ModalProps = {
  open: boolean;
  title: string;
  subtitle?: ReactNode;
  size?: ModalSize;
  padded?: boolean;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  /** @deprecated Use size="lg" */
  wide?: boolean;
};

export function Modal({
  open,
  title,
  subtitle,
  size,
  padded = true,
  onClose,
  children,
  footer,
  wide,
}: ModalProps) {
  const resolvedSize = size ?? (wide ? "lg" : "md");

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="app-modal-overlay" role="presentation" onClick={onClose}>
      <div
        className={`app-modal size-${resolvedSize}${padded ? "" : " unpadded"}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="app-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="app-modal-header">
          <div className="app-modal-heading">
            <h2 id="app-modal-title">{title}</h2>
            {subtitle ? <p className="app-modal-subtitle">{subtitle}</p> : null}
          </div>
          <button type="button" className="app-modal-close" onClick={onClose} aria-label="Close">
            <X size={20} />
          </button>
        </header>
        <div className="app-modal-body">{children}</div>
        {footer ? <footer className="app-modal-footer">{footer}</footer> : null}
      </div>
    </div>,
    document.body,
  );
}
