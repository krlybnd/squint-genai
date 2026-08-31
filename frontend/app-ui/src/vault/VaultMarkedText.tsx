import { sanitizeText } from "@are/ui-core";
import { parseVaultMarks } from "./parseVaultMarks";
import "./VaultMarkedText.css";

interface Props {
  text: string;
  formatTooltip: (token: string) => string;
}

export function VaultMarkedText({ text, formatTooltip }: Props) {
  const parts = parseVaultMarks(text);
  return (
    <>
      {parts.map((part, index) =>
        part.kind === "vault" ? (
          <span
            key={`${part.token}-${index}`}
            className="vault-reveal"
            tabIndex={0}
            aria-label={`${part.value} (${formatTooltip(part.token)})`}
          >
            {sanitizeText(part.value)}
            <span className="vault-reveal-tip" role="tooltip">
              {formatTooltip(part.token)}
            </span>
          </span>
        ) : (
          <span key={`text-${index}`}>{sanitizeText(part.value)}</span>
        ),
      )}
    </>
  );
}
