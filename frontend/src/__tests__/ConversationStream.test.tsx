import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ConversationStream } from "../components/ConversationStream";
import type { ConversationMessage } from "../viewModels/workbenchViewModel";

afterEach(() => cleanup());

const messages: ConversationMessage[] = [
  {
    id: "msg_1",
    actor: "architect",
    actorLabel: "Architect",
    actorType: "agent",
    stage: "draft_design",
    eventType: "agent_output_submitted",
    body: "## Proposed Design\nUse a file-first workflow.",
    timestamp: "2026-06-19T10:00:00Z",
    relatedFile: "agents/architect/draft_response.v1.md",
    runnerLabel: "Codex",
    llmName: "GPT-5.5"
  },
  {
    id: "msg_2",
    actor: "human",
    actorLabel: "Human",
    actorType: "human",
    stage: "clarification",
    eventType: "human_answer_submitted",
    body: "Use natural-language answers.",
    timestamp: "2026-06-19T10:05:00Z",
    relatedFile: null,
    runnerLabel: null,
    llmName: null
  }
];

describe("ConversationStream", () => {
  it("renders agent and human messages as the central discussion", () => {
    render(<ConversationStream messages={messages} />);

    expect(screen.getByLabelText("Agent conversation")).toBeTruthy();
    expect(screen.getByText("Architect")).toBeTruthy();
    expect(screen.getByText("Codex / GPT-5.5")).toBeTruthy();
    expect(screen.getByText("draft_design")).toBeTruthy();
    expect(screen.getByText("Use a file-first workflow.")).toBeTruthy();
    expect(screen.getByText("agents/architect/draft_response.v1.md")).toBeTruthy();
    expect(screen.getByText("Human")).toBeTruthy();
    expect(screen.getByText("Use natural-language answers.")).toBeTruthy();
  });

  it("renders an empty state and natural-language composer", () => {
    render(<ConversationStream messages={[]} />);

    expect(screen.getByText("No conversation yet.")).toBeTruthy();
    expect(screen.getByPlaceholderText("Ask a question or provide additional context...")).toBeTruthy();
  });
});
