import { ChevronLeft, ChevronRight, Loader2, MessageSquare, Trash2 } from "lucide-react";
import type { TFunction } from "i18next";
import type { ChatSession } from "../../../api/types";
import { formatSessionDate } from "../utils";

interface Props {
  t: TFunction;
  sessions: ChatSession[];
  activeSessionId: string | undefined;
  drawerOpen: boolean;
  canWrite: boolean;
  streaming: boolean;
  deletingId: string | null;
  onToggleDrawer: () => void;
  onSelectSession: (session: ChatSession) => void;
  onDeleteSession: (session: ChatSession, e: React.MouseEvent) => void;
}

export function SessionDrawer({
  t,
  sessions,
  activeSessionId,
  drawerOpen,
  canWrite,
  streaming,
  deletingId,
  onToggleDrawer,
  onSelectSession,
  onDeleteSession,
}: Props) {
  return (
    <>
      <button
        type="button"
        className="session-drawer-toggle"
        onClick={onToggleDrawer}
        aria-expanded={drawerOpen}
        aria-label={drawerOpen ? "Close sessions" : "Open sessions"}
      >
        {drawerOpen ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
      </button>

      <aside className={`session-drawer ${drawerOpen ? "open" : ""}`} aria-hidden={!drawerOpen}>
        <div className="session-drawer-header">
          <MessageSquare size={18} />
          <h3>{t("chat.sessionsTitle")}</h3>
        </div>
        <div className="session-drawer-list">
          {sessions.length === 0 && (
            <p className="session-drawer-empty">{t("chat.noSessionsSaved")}</p>
          )}
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`session-drawer-item ${activeSessionId === s.id ? "active" : ""}`}
            >
              <button
                type="button"
                className="session-drawer-select"
                onClick={() => onSelectSession(s)}
                disabled={streaming}
              >
                <span className="session-drawer-title">{s.title ?? t("chat.newChatDefault")}</span>
                <span className="session-drawer-meta">{formatSessionDate(s.updated_at)}</span>
              </button>
              {canWrite && (
                <button
                  type="button"
                  className="session-drawer-delete"
                  title="Delete session"
                  disabled={deletingId === s.id}
                  onClick={(e) => onDeleteSession(s, e)}
                >
                  {deletingId === s.id ? (
                    <Loader2 size={14} className="spin" />
                  ) : (
                    <Trash2 size={14} />
                  )}
                </button>
              )}
            </div>
          ))}
        </div>
      </aside>
    </>
  );
}
