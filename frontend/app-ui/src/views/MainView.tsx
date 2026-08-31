import { useEffect, useState } from "react";
import { AppShell, useTenant } from "@are/ui-core";
import { getAppFeatures } from "@are/ui-core/app/appConfigStore";
import { ChatSession } from "../api/client";
import { ChatPanel } from "../features/chat/ChatPanel";
import { DocumentsPanel } from "../components/DocumentsPanel";
import "../App.css";

export default function MainView() {
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const { tenantId } = useTenant();

  useEffect(() => {
    setActiveSession(null);
  }, [tenantId]);

  const adminPanelHref = getAppFeatures()?.adminPanelHref;

  return (
    <AppShell
      sidebar={<DocumentsPanel key={tenantId ?? "none"} />}
      profileMenu={adminPanelHref ? { adminPanelHref } : undefined}
    >
      <div className="chat-area">
        <ChatPanel key={tenantId ?? "none"} session={activeSession} onSessionCreated={setActiveSession} />
      </div>
    </AppShell>
  );
}
