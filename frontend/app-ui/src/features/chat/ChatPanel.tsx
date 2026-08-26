import type { ChatSession } from "../../api/types";
import { ChunkViewerModal } from "../../components/ChunkViewerModal";
import { ChatInputArea } from "./components/ChatInputArea";
import { ChatToolbar } from "./components/ChatToolbar";
import { MessageList } from "./components/MessageList";
import { ReasoningNotebook } from "./components/ReasoningNotebook";
import { SessionDrawer } from "./components/SessionDrawer";
import { useChatController } from "./hooks/useChatController";
import "./ChatPanel.css";

interface Props {
  session: ChatSession | null;
  onSessionCreated: (s: ChatSession | null) => void;
}

export function ChatPanel({ session, onSessionCreated }: Props) {
  const c = useChatController({ session, onSessionCreated });

  return (
    <div className={`chat-panel ${c.drawerOpen ? "drawer-open" : ""}`}>
      <div className="chat-panel-body">
        <ChatToolbar
          t={c.t}
          sessionTitle={c.sessionTitle}
          canWrite={c.canWrite}
          streaming={c.streaming}
          onNewChat={() => void c.handleNewChat()}
        />

        <div className="chat-main" ref={c.chatMainRef}>
          <MessageList
            t={c.t}
            messages={c.messages}
            streaming={c.streaming}
            streamText={c.streamText}
            canWrite={c.canWrite}
            bottomRef={c.bottomRef}
            getMessageText={c.getMessageText}
            onEditMessage={(id, content) =>
              c.setMessageEdits((prev) => ({ ...prev, [id]: content }))
            }
            onResendMessage={(m, idx) => void c.handleUserMessageResend(m, idx)}
            onOpenCitation={c.openCitation}
          />

          <ReasoningNotebook
            t={c.t}
            reasoningRuns={c.reasoningRuns}
            reasoningOpen={c.reasoningOpen}
            panelBodyHeight={c.panelBodyHeight}
            streaming={c.streaming}
            status={c.status}
            canWrite={c.canWrite}
            reasoningLogRef={c.reasoningLogRef}
            onToggleOpen={() => c.setReasoningOpen((o) => !o)}
            onReplay={c.handleReplay}
            onOpenChunk={c.openReasoningChunk}
            onResizeStart={c.startReasoningResize}
          />

          <ChatInputArea
            t={c.t}
            input={c.input}
            canWrite={c.canWrite}
            streaming={c.streaming}
            error={c.error}
            onInputChange={c.setInput}
            onSend={() => void c.handleSend()}
            onPause={c.handlePause}
          />
        </div>
      </div>

      <SessionDrawer
        t={c.t}
        sessions={c.sessions}
        activeSessionId={c.session?.id}
        drawerOpen={c.drawerOpen}
        canWrite={c.canWrite}
        streaming={c.streaming}
        deletingId={c.deletingId}
        onToggleDrawer={() => c.setDrawerOpen((open) => !open)}
        onSelectSession={c.handleSelectSession}
        onDeleteSession={(s, e) => void c.handleDeleteSession(s, e)}
      />

      {c.chunkViewer && (
        <ChunkViewerModal
          docId={c.chunkViewer.docId}
          sourceFile={c.chunkViewer.sourceFile}
          initialChunkId={c.chunkViewer.chunkId}
          canWrite={c.canWrite}
          onClose={() => c.setChunkViewer(null)}
        />
      )}
    </div>
  );
}
