import { Pause, Send } from "lucide-react";
import type { TFunction } from "i18next";
import { AutoGrowTextarea } from "./AutoGrowTextarea";

interface Props {
  t: TFunction;
  input: string;
  canWrite: boolean;
  streaming: boolean;
  error: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onPause: () => void;
}

export function ChatInputArea({
  t,
  input,
  canWrite,
  streaming,
  error,
  onInputChange,
  onSend,
  onPause,
}: Props) {
  return (
    <div className="chat-input-area">
      {error && (
        <div className="chat-error" role="alert">
          {error}
        </div>
      )}
      <AutoGrowTextarea
        value={input}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (!streaming) onSend();
          }
        }}
        placeholder={canWrite ? t("chat.placeholder") : t("chat.placeholderReadOnly")}
        minRows={2}
        disabled={!canWrite}
      />
      {streaming ? (
        <button
          type="button"
          className="btn-send btn-pause"
          onClick={onPause}
          title={t("chat.stopGeneration")}
          aria-label={t("chat.stopGeneration")}
        >
          <Pause size={18} />
        </button>
      ) : (
        <button
          type="button"
          className="btn-send"
          onClick={onSend}
          disabled={!canWrite || !input.trim()}
        >
          <Send size={18} />
        </button>
      )}
    </div>
  );
}
