export type VaultTextPart =
  | { kind: "text"; value: string }
  | { kind: "vault"; value: string; token: string };

const VAULT_MARK_RE =
  /\[\[vault:(<[A-Z0-9_]+_[A-F0-9]{8}>)\]\]([\s\S]*?)\[\[\/vault\]\]/g;
const VAULT_MARK_OPEN = "[[vault:";
const VAULT_MARK_CLOSE = "[[/vault]]";

export function parseVaultMarks(text: string): VaultTextPart[] {
  const parts: VaultTextPart[] = [];
  const re = new RegExp(VAULT_MARK_RE.source, "g");
  let last = 0;
  let match = re.exec(text);
  while (match !== null) {
    if (match.index > last) {
      parts.push({ kind: "text", value: text.slice(last, match.index) });
    }
    parts.push({ kind: "vault", value: match[2] ?? "", token: match[1] ?? "" });
    last = match.index + match[0].length;
    match = re.exec(text);
  }
  const leftover = text.slice(last);
  const pendingIdx = leftover.lastIndexOf(VAULT_MARK_OPEN);
  if (pendingIdx !== -1 && leftover.indexOf(VAULT_MARK_CLOSE, pendingIdx) === -1) {
    if (pendingIdx > 0) {
      parts.push({ kind: "text", value: leftover.slice(0, pendingIdx) });
    }
    return parts;
  }
  if (leftover) {
    parts.push({ kind: "text", value: leftover });
  }
  return parts;
}

export function stripVaultMarks(text: string): string {
  return parseVaultMarks(text)
    .map((part) => part.value)
    .join("");
}
