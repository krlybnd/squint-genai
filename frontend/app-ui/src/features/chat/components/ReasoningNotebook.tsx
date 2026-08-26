import { Brain, ChevronDown, ChevronUp, Loader2, RotateCcw } from "lucide-react";
import type { TFunction } from "i18next";
import { sanitizeText } from "@are/ui-core";
import type { ReasoningRun } from "../types";
import { formatReasoningSeparator } from "../utils";
import { ReasoningLineItem } from "./ReasoningLineItem";

interface Props {
  t: TFunction;
  reasoningRuns: ReasoningRun[];
  reasoningOpen: boolean;
  panelBodyHeight: number;
  streaming: boolean;
  status: string;
  canWrite: boolean;
  reasoningLogRef: React.RefObject<HTMLUListElement | null>;
  onToggleOpen: () => void;
  onReplay: (run: ReasoningRun, checkpointId?: string | null, fromStep?: string) => void;
  onOpenChunk: (chunk: import("../../../api/types").ChunkPreview) => void;
  onResizeStart: (e: React.MouseEvent) => void;
}

export function ReasoningNotebook({
  t,
  reasoningRuns,
  reasoningOpen,
  panelBodyHeight,
  streaming,
  status,
  canWrite,
  reasoningLogRef,
  onToggleOpen,
  onReplay,
  onOpenChunk,
  onResizeStart,
}: Props) {
  return (
    <div
      className={`reasoning-notebook ${reasoningOpen ? "open" : "collapsed"}`}
      style={{ height: panelBodyHeight }}
    >
      {reasoningOpen && (
        <div
          className="reasoning-resizer"
          role="separator"
          aria-orientation="horizontal"
          aria-label="Resize reasoning panel"
          onMouseDown={onResizeStart}
        />
      )}
      <section className="reasoning-panel" aria-label="Agent reasoning notebook">
        <button
          type="button"
          className="reasoning-panel-header"
          onClick={onToggleOpen}
          aria-expanded={reasoningOpen}
        >
          <Brain size={16} />
          <span>{t("chat.reasoning")}</span>
          {streaming && <Loader2 size={14} className="spin reasoning-header-spin" />}
          <span className="reasoning-toggle-icon">
            {reasoningOpen ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
          </span>
        </button>
        {reasoningOpen && (
          <ul className="reasoning-log" ref={reasoningLogRef}>
            {reasoningRuns.length === 0 && (
              <li className="reasoning-empty">{t("chat.reasoningEmpty")}</li>
            )}
            {reasoningRuns.map((run) => (
              <li key={run.id} className="reasoning-run">
                <div className="reasoning-separator">
                  <button
                    type="button"
                    className="chat-retry-btn"
                    title={t("chat.retryRun")}
                    aria-label={t("chat.retryRun")}
                    disabled={streaming || !canWrite}
                    onClick={() => onReplay(run, null)}
                  >
                    <RotateCcw size={12} />
                  </button>
                  <span className="reasoning-separator-line" aria-hidden />
                  <button
                    type="button"
                    className="reasoning-separator-time"
                    title={t("chat.jumpToRun")}
                    disabled={streaming || !canWrite}
                    onClick={() => onReplay(run, null)}
                  >
                    <time dateTime={run.at}>{formatReasoningSeparator(run.at)}</time>
                  </button>
                  <span className="reasoning-separator-line" aria-hidden />
                </div>
                {run.query && (
                  <p className="reasoning-run-query">{sanitizeText(run.query)}</p>
                )}
                <ul className="reasoning-run-lines">
                  {run.lines.map((line) => (
                    <ReasoningLineItem
                      key={`${run.id}-${line.step}`}
                      t={t}
                      run={run}
                      line={line}
                      status={status}
                      canWrite={canWrite}
                      streaming={streaming}
                      onReplay={onReplay}
                      onOpenChunk={onOpenChunk}
                    />
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
