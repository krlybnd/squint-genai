import { Sparkles } from "lucide-react";
import type { TFunction } from "i18next";
import { sanitizeText } from "@are/ui-core";

interface Props {
  t: TFunction;
  sessionTitle: string | null;
  canWrite: boolean;
  streaming: boolean;
  onNewChat: () => void;
}

export function ChatToolbar({ t, sessionTitle, canWrite, streaming, onNewChat }: Props) {
  return (
    <div className="chat-toolbar">
      <button className="btn-new-chat" onClick={onNewChat} disabled={!canWrite || streaming}>
        <Sparkles size={16} /> {t("chat.newChat")}
      </button>
      <div className="chat-toolbar-spacer" />
      {sessionTitle && (
        <span className="chat-session-title" key={sessionTitle}>
          {sanitizeText(sessionTitle)}
        </span>
      )}
    </div>
  );
}
