import type { TFunction } from "i18next";
import type { SearchMeta } from "../../api/types";

export function stepLabel(t: TFunction, step: string): string {
  const key = `reasoning.steps.${step}`;
  const translated = t(key);
  return translated === key ? step : translated;
}

export function piiKindLabel(t: TFunction, kind: string): string {
  const key = `pii.${kind}`;
  const translated = t(key);
  return translated === key ? kind : translated;
}

export function renderSearchMetaRows(
  meta: SearchMeta,
  t: TFunction,
): { label: string; value: string }[] {
  if (meta.skipped) {
    return [{ label: t("reasoning.skippedLabel"), value: meta.reason || "—" }];
  }
  const yes = t("reasoning.yes");
  const no = t("reasoning.no");
  const rows: { label: string; value: string }[] = [
    {
      label: t("reasoning.searchType"),
      value: meta.search_type === "hybrid" ? t("reasoning.hybrid") : meta.search_type || "—",
    },
    { label: t("reasoning.dense"), value: meta.dense ? `${yes} (${meta.dense_model || "?"})` : no },
    { label: t("reasoning.sparse"), value: meta.sparse ? `${yes} (${meta.sparse_model || "?"})` : no },
    { label: t("reasoning.fusion"), value: (meta.fusion || "—").toUpperCase() },
    { label: t("reasoning.candidatesTopK"), value: String(meta.candidate_top_k ?? "—") },
    { label: t("reasoning.finalTopK"), value: String(meta.final_top_k ?? "—") },
    { label: t("reasoning.rrfCandidates"), value: String(meta.candidates_found ?? "—") },
    {
      label: t("reasoning.rerank"),
      value: meta.rerank_applied
        ? t("reasoning.rerankOn", { model: meta.rerank_model || "?" })
        : meta.rerank_enabled
          ? t("reasoning.rerankError", { error: meta.rerank_error || "?" })
          : t("reasoning.rerankOff"),
    },
    { label: t("reasoning.results"), value: String(meta.results_count ?? "—") },
  ];
  if (meta.search_query) {
    rows.unshift({ label: t("reasoning.searchQuery"), value: meta.search_query });
  }
  if (meta.error) {
    rows.push({ label: t("reasoning.error"), value: meta.error });
  }
  return rows;
}

export function formatSessionDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const sameDay =
    d.getDate() === now.getDate() &&
    d.getMonth() === now.getMonth() &&
    d.getFullYear() === now.getFullYear();
  if (sameDay) {
    return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  }
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function formatReasoningSeparator(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function isDefaultSessionTitle(
  title: string | null | undefined,
  newChatDefault: string,
): boolean {
  if (!title?.trim()) return true;
  return title === "New chat" || title === newChatDefault;
}
