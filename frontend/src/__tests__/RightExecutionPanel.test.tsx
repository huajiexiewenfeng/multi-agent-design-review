import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RightExecutionPanel } from "../components/RightExecutionPanel";
import type {
  AgentQueueItem,
  FinalOutputItem,
  HumanActionItem,
  WorkbenchArtifact
} from "../viewModels/workbenchViewModel";

afterEach(() => cleanup());

const agentQueue: AgentQueueItem[] = [
  {
    id: "architect",
    label: "Architect",
    runnerLabel: "Codex",
    llmName: "GPT-5.5",
    status: "in_progress",
    task: "Working on Draft"
  }
];

const humanActions: HumanActionItem[] = [
  {
    id: "human_action_1",
    title: "Human input required",
    description: "Answer reviewer questions.",
    missingInput: "input/human_answers.json"
  }
];

const artifacts: WorkbenchArtifact[] = [
  { path: "agents/architect/draft_response.v1.md", kind: "output", agentId: "architect" }
];

const finalOutputs: FinalOutputItem[] = [
  { path: "output/design_doc.md", label: "Design Doc", exists: true, ready: true },
  { path: "output/execution_doc.md", label: "Execution Doc", exists: false, ready: false }
];

describe("RightExecutionPanel", () => {
  it("renders queue, human actions, artifacts, final outputs, and debug access", () => {
    render(
      <RightExecutionPanel
        agentQueue={agentQueue}
        humanActions={humanActions}
        artifacts={artifacts}
        finalOutputs={finalOutputs}
        canFinalize
        isImportingHandoffs={false}
        onFinalize={vi.fn()}
        onImportHandoffs={vi.fn()}
      />
    );

    expect(screen.getByLabelText("Execution panel")).toBeTruthy();
    expect(screen.getByText("Agent Queue")).toBeTruthy();
    expect(screen.getByText("Architect")).toBeTruthy();
    expect(screen.getByText("Codex / GPT-5.5")).toBeTruthy();
    expect(screen.getByText("Human Action Required")).toBeTruthy();
    expect(screen.getByText("Answer reviewer questions.")).toBeTruthy();
    expect(screen.getByText("Artifacts")).toBeTruthy();
    expect(screen.getByText("agents/architect/draft_response.v1.md")).toBeTruthy();
    expect(screen.getByText("Final Outputs")).toBeTruthy();
    expect(screen.getByText("Design Doc")).toBeTruthy();
    expect(screen.getByText("Debug")).toBeTruthy();
  });

  it("calls finalize and import actions", () => {
    const onFinalize = vi.fn();
    const onImportHandoffs = vi.fn();
    render(
      <RightExecutionPanel
        agentQueue={agentQueue}
        humanActions={[]}
        artifacts={[]}
        finalOutputs={finalOutputs}
        canFinalize
        isImportingHandoffs={false}
        onFinalize={onFinalize}
        onImportHandoffs={onImportHandoffs}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Generate final docs" }));
    fireEvent.click(screen.getByRole("button", { name: "Check runner outputs" }));

    expect(onFinalize).toHaveBeenCalledOnce();
    expect(onImportHandoffs).toHaveBeenCalledOnce();
  });

  it("submits human action content as natural language", () => {
    const onSubmitHumanInput = vi.fn();
    render(
      <RightExecutionPanel
        agentQueue={agentQueue}
        humanActions={humanActions}
        artifacts={artifacts}
        finalOutputs={finalOutputs}
        canFinalize={false}
        isImportingHandoffs={false}
        onFinalize={vi.fn()}
        onImportHandoffs={vi.fn()}
        onSubmitHumanInput={onSubmitHumanInput}
      />
    );

    fireEvent.change(screen.getByLabelText("Human response"), {
      target: { value: "我希望 MVP 先支持本地 Codex 和 Claude Code 自动协作。" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Save response" }));

    expect(onSubmitHumanInput).toHaveBeenCalledWith(
      humanActions[0],
      "我希望 MVP 先支持本地 Codex 和 Claude Code 自动协作。"
    );
  });

  it("opens and previews final output content", () => {
    const onOpenFinalOutput = vi.fn();
    const onCopyFinalOutput = vi.fn();
    const onDownloadFinalOutput = vi.fn();
    render(
      <RightExecutionPanel
        agentQueue={agentQueue}
        humanActions={[]}
        artifacts={artifacts}
        finalOutputs={finalOutputs}
        finalOutputPreviews={{ "output/design_doc.md": "# Design Doc\n\nReady." }}
        canFinalize={false}
        isImportingHandoffs={false}
        onFinalize={vi.fn()}
        onImportHandoffs={vi.fn()}
        onOpenFinalOutput={onOpenFinalOutput}
        onCopyFinalOutput={onCopyFinalOutput}
        onDownloadFinalOutput={onDownloadFinalOutput}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Open Design Doc" }));
    fireEvent.click(screen.getByRole("button", { name: "Copy Design Doc path" }));
    fireEvent.click(screen.getByRole("button", { name: "Download Design Doc" }));

    expect(onOpenFinalOutput).toHaveBeenCalledWith(finalOutputs[0]);
    expect(onCopyFinalOutput).toHaveBeenCalledWith(finalOutputs[0]);
    expect(onDownloadFinalOutput).toHaveBeenCalledWith(finalOutputs[0]);
    expect(screen.getByText("# Design Doc")).toBeTruthy();
    expect(screen.getByText("Ready.")).toBeTruthy();
  });
});
