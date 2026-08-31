import { useEffect, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import "./Select.css";

export type SelectOption<T extends string = string> = {
  value: T;
  label: string;
};

export type SelectVariant = "header" | "form";

export type SelectProps<T extends string = string> = {
  value: T;
  options: SelectOption<T>[];
  onChange: (value: T) => void;
  ariaLabel: string;
  variant?: SelectVariant;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  menuPlacement?: "up" | "down";
};

export function Select<T extends string = string>({
  value,
  options,
  onChange,
  ariaLabel,
  variant = "form",
  disabled = false,
  placeholder,
  className,
  menuPlacement = "down",
}: SelectProps<T>) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const selected = options.find((opt) => opt.value === value);
  const displayLabel = selected?.label ?? (value ? value : (placeholder ?? ariaLabel));
  const isPlaceholder = !value;

  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const rootClass = [
    "ui-select",
    variant,
    disabled ? "disabled" : "",
    open ? "open" : "",
    menuPlacement === "up" ? "menu-up" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass} ref={rootRef}>
      <button
        type="button"
        className={`ui-select-trigger${isPlaceholder ? " placeholder" : ""}`}
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        disabled={disabled}
        onClick={() => !disabled && setOpen((prev) => !prev)}
      >
        <span className="ui-select-label">{displayLabel}</span>
        <ChevronDown size={14} className={`ui-select-chevron${open ? " open" : ""}`} />
      </button>
      {open && !disabled && (
        <div className="ui-select-menu" role="listbox" aria-label={ariaLabel}>
          {options.map((opt) => (
            <button
              key={opt.value || "__empty__"}
              type="button"
              role="option"
              aria-selected={opt.value === value}
              className={`ui-select-option${opt.value === value ? " active" : ""}`}
              onClick={() => {
                onChange(opt.value);
                setOpen(false);
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/** @deprecated Use Select with variant="header" */
export function HeaderSelect<T extends string>(props: Omit<SelectProps<T>, "variant">) {
  return <Select {...props} variant="header" />;
}
