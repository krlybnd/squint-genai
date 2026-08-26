import { cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ChatSession } from "../../../api/types";
import { useChatController } from "./useChatController";

const fetchSessions = vi.fn();
const fetchMessages = vi.fn();
const createSession = vi.fn();
const deleteSession = vi.fn();
const streamChat = vi.fn();
const streamReplay = vi.fn();
const truncateMessagesFrom = vi.fn();

vi.mock("../../../api/client", () => ({
  fetchSessions: (...args: unknown[]) => fetchSessions(...args),
  fetchMessages: (...args: unknown[]) => fetchMessages(...args),
  createSession: (...args: unknown[]) => createSession(...args),
  deleteSession: (...args: unknown[]) => deleteSession(...args),
  streamChat: (...args: unknown[]) => streamChat(...args),
  streamReplay: (...args: unknown[]) => streamReplay(...args),
  truncateMessagesFrom: (...args: unknown[]) => truncateMessagesFrom(...args),
}));

vi.mock("@are/ui-core", () => ({
  useAuth: () => ({
    hasAnyRole: () => true,
  }),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

const session: ChatSession = {
  id: "session-1",
  title: "Chat",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
} as ChatSession;

describe("useChatController", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("loads sessions on mount", async () => {
    // Arrange
    fetchSessions.mockResolvedValue([session]);

    // Act
    const { result } = renderHook(() =>
      useChatController({ session: null, onSessionCreated: vi.fn() }),
    );

    // Assert
    await waitFor(() => {
      expect(result.current.sessions).toEqual([session]);
    });
    expect(fetchSessions).toHaveBeenCalledTimes(1);
  });

  it("clears messages when the active session is removed", async () => {
    // Arrange
    fetchSessions.mockResolvedValue([session]);
    fetchMessages.mockResolvedValue([
      {
        id: "m1",
        role: "user",
        content: "hello",
        created_at: "2026-01-01T00:00:00Z",
      },
    ]);

    const { result, rerender } = renderHook(
      ({ active }: { active: ChatSession | null }) =>
        useChatController({ session: active, onSessionCreated: vi.fn() }),
      { initialProps: { active: session } },
    );

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(1);
    });

    // Act
    rerender({ active: null });

    // Assert
    await waitFor(() => {
      expect(result.current.messages).toEqual([]);
    });
    expect(result.current.sessionTitle).toBeNull();
  });
});
