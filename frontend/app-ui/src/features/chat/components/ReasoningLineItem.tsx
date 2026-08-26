import { Loader2, RotateCcw } from "lucide-react";
import type { TFunction } from "i18next";
import { sanitizeText } from "@are/ui-core";
import type { ReasoningLine, ReasoningRun } from "../types";
import { piiKindLabel, renderSearchMetaRows, stepLabel } from "../utils";
import { ReasoningChunkList } from "./ReasoningChunkList";

interface Props {
  t: TFunction;
  run: ReasoningRun;
  line: ReasoningLine;
  status: string;
  canWrite: boolean;
  streaming: boolean;
  onReplay: (run: ReasoningRun, checkpointId?: string | null, fromStep?: string) => void;
  onOpenChunk: (chunk: import("../../../api/types").ChunkPreview) => void;
}

export function ReasoningLineItem({
  t,
  run,
  line,
  status,
  canWrite,
  streaming,
  onReplay,
  onOpenChunk,
}: Props) {
  return (
    <li
      className={`reasoning-line ${line.status}${line.step === status ? " current" : ""}`}
    >
      {line.status === "done" && line.checkpointId ? (
        <button
          type="button"
          className="chat-retry-btn chat-retry-btn-sm"
          title={t("chat.retryFromStep")}
          aria-label={`${t("chat.retryFromStep")}: ${stepLabel(t, line.step)}`}
          disabled={streaming || !canWrite}
          onClick={() => onReplay(run, line.checkpointId, line.step)}
        >
          <RotateCcw size={11} />
        </button>
      ) : (
        <span className="chat-retry-btn-spacer" aria-hidden />
      )}
      <div className="reasoning-line-body">
        <div className="reasoning-line-main">
          <span className="reasoning-step">{stepLabel(t, line.step)}</span>
          <span className="reasoning-message">{sanitizeText(line.message)}</span>
          {line.status === "active" && <Loader2 size={12} className="spin reasoning-spin" />}
        </div>
        {line.step === "guard" && line.status === "done" && (line.piiRedactions ?? 0) > 0 && (
          <details className="reasoning-guard-accordion">
            <summary>{t("reasoning.maskingDetails", { count: line.piiRedactions })}</summary>
            <div className="reasoning-guard-accordion-body">
              {line.safeQuery && (
                <div className="reasoning-guard-block">
                  <span className="reasoning-guard-label">{t("reasoning.textToProvider")}</span>
                  <pre>{sanitizeText(line.safeQuery)}</pre>
                </div>
              )}
              {run.query && (
                <div className="reasoning-guard-block">
                  <span className="reasoning-guard-label">{t("reasoning.originalQuestion")}</span>
                  <pre>{sanitizeText(run.query)}</pre>
                </div>
              )}
              {(line.piiDetails?.length ?? 0) > 0 && (
                <ul className="reasoning-pii-list">
                  {line.piiDetails!.map((d, i) => (
                    <li key={`${d.kind}-${i}`}>
                      <span className="reasoning-pii-kind">{piiKindLabel(t, d.kind)}</span>
                      <span className="reasoning-pii-arrow">→</span>
                      <code>{sanitizeText(d.placeholder)}</code>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </details>
        )}
        {line.step === "rewrite" && line.status === "done" && (
          <details className="reasoning-guard-accordion">
            <summary>{t("reasoning.routingDetails")}</summary>
            <div className="reasoning-guard-accordion-body">
              <ul className="reasoning-meta-list">
                <li>
                  <span className="reasoning-guard-label">{t("reasoning.documentSearch")}</span>
                  <span>{line.needsRetrieval ? t("reasoning.yes") : t("reasoning.no")}</span>
                </li>
                {(line.indexedDocumentCount ?? 0) > 0 && (
                  <li>
                    <span className="reasoning-guard-label">{t("reasoning.indexedDocs")}</span>
                    <span>{line.indexedDocumentCount}</span>
                  </li>
                )}
                {line.searchQuery && (
                  <li>
                    <span className="reasoning-guard-label">{t("reasoning.searchQuery")}</span>
                    <span>{sanitizeText(line.searchQuery)}</span>
                  </li>
                )}
                {line.rewriteReason && (
                  <li>
                    <span className="reasoning-guard-label">{t("reasoning.reason")}</span>
                    <span>{sanitizeText(line.rewriteReason)}</span>
                  </li>
                )}
              </ul>
            </div>
          </details>
        )}
        {line.step === "retrieve" && line.status === "done" && line.searchMeta && (
          <details className="reasoning-guard-accordion">
            <summary>
              {t("reasoning.searchDetails")}
              {line.searchMeta.skipped ? t("reasoning.skipped") : ""}
            </summary>
            <div className="reasoning-guard-accordion-body">
              <ul className="reasoning-meta-list">
                {renderSearchMetaRows(line.searchMeta, t).map((row) => (
                  <li key={row.label}>
                    <span className="reasoning-guard-label">{row.label}</span>
                    <span>{sanitizeText(row.value)}</span>
                  </li>
                ))}
              </ul>
              {!line.searchMeta.skipped && (
                <>
                  <ReasoningChunkList
                    title={t("reasoning.rrfList")}
                    chunks={line.searchMeta.rrf_candidates ?? []}
                    onOpenChunk={onOpenChunk}
                    openLabel={t("reasoning.openChunk")}
                    topKLabel={t("reasoning.topK")}
                    pageLabel={t("chat.page")}
                  />
                  <ReasoningChunkList
                    title={t("reasoning.finalList")}
                    chunks={line.searchMeta.final_chunks ?? []}
                    onOpenChunk={onOpenChunk}
                    openLabel={t("reasoning.openChunk")}
                    topKLabel={t("reasoning.topK")}
                    pageLabel={t("chat.page")}
                  />
                </>
              )}
            </div>
          </details>
        )}
      </div>
    </li>
  );
}
