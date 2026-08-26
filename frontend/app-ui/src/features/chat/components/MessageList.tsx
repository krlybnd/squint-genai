import { RotateCcw, Sparkles } from "lucide-react";
import type { TFunction } from "i18next";
import type { ChatMessage, Citation } from "../../../api/types";
import { sanitizeText } from "@are/ui-core";

interface Props {
  t: TFunction;
  messages: ChatMessage[];
  streaming: boolean;
  streamText: string;
  canWrite: boolean;
  bottomRef: React.RefObject<HTMLDivElement | null>;
  getMessageText: (message: ChatMessage) => string;
  onEditMessage: (messageId: string, content: string) => void;
  onResendMessage: (message: ChatMessage, index: number) => void;
  onOpenCitation: (citation: Citation) => void;
}

export function MessageList({
  t,
  messages,
  streaming,
  streamText,
  canWrite,
  bottomRef,
  getMessageText,
  onEditMessage,
  onResendMessage,
  onOpenCitation,
}: Props) {
  return (
    <div className="chat-messages">
      {messages.length === 0 && !streaming && (
        <div className="chat-empty">
          <Sparkles size={48} strokeWidth={1.5} />
          <h2>{t("chat.emptyTitle")}</h2>
          <p>{t("chat.emptySubtitle")}</p>
        </div>
      )}
      {messages.map((m, messageIndex) => (
        <div key={m.id} className={`message ${m.role}`}>
          {m.role === "user" ? (
            <div className="message-row">
              <button
                type="button"
                className="chat-retry-btn"
                title={t("chat.resendMessage")}
                aria-label={t("chat.resendMessage")}
                disabled={streaming || !canWrite}
                onClick={() => void onResendMessage(m, messageIndex)}
              >
                <RotateCcw size={12} />
              </button>
              <textarea
                className="message-bubble message-bubble-editable"
                value={getMessageText(m)}
                onChange={(e) => onEditMessage(m.id, e.target.value)}
                rows={Math.min(8, Math.max(1, getMessageText(m).split("\n").length))}
                disabled={streaming || !canWrite}
              />
            </div>
          ) : (
            <div className="message-bubble">{sanitizeText(m.content)}</div>
          )}
          {(m.citations?.length ?? 0) > 0 && (
            <div className="citations">
              <span className="citations-label">{t("chat.citationsLabel")}</span>
              <div className="citation-chips">
                {m.citations!.map((c, i) => (
                  <button
                    key={`${c.chunk_id || i}-${c.page}`}
                    type="button"
                    className="citation-chip"
                    onClick={() => onOpenCitation(c as Citation)}
                    title={t("chat.citationTitle")}
                  >
                    {sanitizeText(c.source_file)} {t("chat.page")}
                    {c.page ?? "?"}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
      {streaming && streamText && (
        <div className="message assistant">
          <div className="message-bubble streaming">{sanitizeText(streamText)}</div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
