import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { createRef } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ChatMessage } from "../../../api/types";
import { MessageList } from "./MessageList";

const t = (key: string) => key;

function userMessage(overrides: Partial<ChatMessage> = {}): ChatMessage {
  return {
    id: "m1",
    role: "user",
    content: "hello",
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  } as ChatMessage;
}

function assistantMessage(overrides: Partial<ChatMessage> = {}): ChatMessage {
  return {
    id: "m2",
    role: "assistant",
    content: "<b>hi</b>",
    created_at: "2026-01-01T00:00:00Z",
    citations: [
      {
        chunk_id: "c1",
        source_file: "doc.pdf",
        page: 2,
      },
    ],
    ...overrides,
  } as ChatMessage;
}

describe("MessageList", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders the empty state when there are no messages", () => {
    // Arrange
    render(
      <MessageList
        t={t}
        messages={[]}
        streaming={false}
        streamText=""
        canWrite={true}
        bottomRef={createRef<HTMLDivElement>()}
        getMessageText={(m) => m.content}
        onEditMessage={vi.fn()}
        onResendMessage={vi.fn()}
        onOpenCitation={vi.fn()}
      />,
    );

    // Act
    const emptyTitle = screen.getByText("chat.emptyTitle");

    // Assert
    expect(emptyTitle).toBeTruthy();
  });

  it("renders assistant punctuation as text and exposes citation chips", () => {
    // Arrange
    const onOpenCitation = vi.fn();
    render(
      <MessageList
        t={t}
        messages={[userMessage(), assistantMessage()]}
        streaming={false}
        streamText=""
        canWrite={true}
        bottomRef={createRef<HTMLDivElement>()}
        getMessageText={(m) => m.content}
        onEditMessage={vi.fn()}
        onResendMessage={vi.fn()}
        onOpenCitation={onOpenCitation}
      />,
    );

    // Act
    screen.getByRole("button", { name: /doc.pdf/ }).click();

    // Assert
    expect(screen.getByText("<b>hi</b>")).toBeTruthy();
    expect(onOpenCitation).toHaveBeenCalled();
  });

  it("renders the streaming assistant bubble while tokens arrive", () => {
    // Arrange
    render(
      <MessageList
        t={t}
        messages={[]}
        streaming={true}
        streamText="it's a & b"
        canWrite={true}
        bottomRef={createRef<HTMLDivElement>()}
        getMessageText={(m) => m.content}
        onEditMessage={vi.fn()}
        onResendMessage={vi.fn()}
        onOpenCitation={vi.fn()}
      />,
    );

    // Act
    const streamingBubble = screen.getByText("it's a & b");

    // Assert
    expect(streamingBubble.className).toContain("streaming");
  });

  it("forwards user edits and resend actions", () => {
    // Arrange
    const onEditMessage = vi.fn();
    const onResendMessage = vi.fn();
    const { container } = render(
      <MessageList
        t={t}
        messages={[userMessage({ content: "draft" })]}
        streaming={false}
        streamText=""
        canWrite={true}
        bottomRef={createRef<HTMLDivElement>()}
        getMessageText={(m) => m.content}
        onEditMessage={onEditMessage}
        onResendMessage={onResendMessage}
        onOpenCitation={vi.fn()}
      />,
    );

    // Act
    fireEvent.change(screen.getByDisplayValue("draft"), { target: { value: "updated" } });
    fireEvent.click(container.querySelector(".chat-retry-btn")!);

    // Assert
    expect(onEditMessage).toHaveBeenCalledWith("m1", "updated");
    expect(onResendMessage).toHaveBeenCalled();
  });
});
