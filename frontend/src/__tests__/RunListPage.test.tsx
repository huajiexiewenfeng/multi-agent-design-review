import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { readRunFile, saveClarificationAnswers } from "../api/client";
import { RunListPage } from "../pages/RunListPage";

vi.mock("../api/client", () => {
  const run = {
    run_id: "run_1",
    stage: "draft_design",
    status: "waiting_input",
    missing_inputs: ["input/human_answers.json"],
    agents: [
      { id: "architect", label: "Architect", runner: "codex", llm_name: "GPT-5.5", stages: ["draft_design"] }
    ]
  };

  return {
    createRun: vi.fn().mockResolvedValue(run),
    finalizeRun: vi.fn().mockResolvedValue(run),
    getEvents: vi.fn().mockResolvedValue([
      {
        id: "evt_1",
        actor: "architect",
        actor_type: "agent",
        event_type: "agent_output_submitted",
        message: "Draft submitted",
        stage: "draft_design",
        related_file: "agents/architect/draft_response.v1.md"
      }
    ]),
    getFlowVerification: vi.fn().mockResolvedValue({
      run_id: "run_1",
      complete: false,
      final_outputs_ready: false,
      final_outputs: [
        { path: "output/design_doc.md", exists: true, non_empty: true, ready: true },
        { path: "output/execution_doc.md", exists: false, non_empty: false, ready: false },
        { path: "output/transcript.md", exists: false, non_empty: false, ready: false }
      ],
      runners: []
    }),
    getGraphJob: vi.fn(),
    getRun: vi.fn().mockResolvedValue(run),
    getRunners: vi.fn().mockResolvedValue([]),
    getRunnerHandoffs: vi.fn().mockResolvedValue([]),
    getRunnerLogs: vi.fn().mockResolvedValue([]),
    getRunnerSmokeJob: vi.fn(),
    getStageArtifacts: vi.fn().mockResolvedValue([
      {
        path: "agents/architect/draft_response.v1.md",
        kind: "output",
        agent_id: "architect",
        content: "## Proposed Design\nA v2 workbench"
      }
    ]),
    importRunnerHandoffs: vi.fn(),
    listRuns: vi.fn().mockResolvedValue([run]),
    readRunFile: vi.fn().mockResolvedValue({ path: "output/design_doc.md", content: "# Design Doc\n\nReady." }),
    saveClarificationAnswers: vi.fn().mockResolvedValue(run),
    saveClarifiedRequirement: vi.fn().mockResolvedValue(run),
    skipAgent: vi.fn().mockResolvedValue(run),
    startGraphStepJob: vi.fn(),
    startRunUntilPauseJob: vi.fn(),
    startRunnerSmokeJob: vi.fn(),
    submitAgentOutput: vi.fn(),
    updateAgentConfig: vi.fn().mockResolvedValue(run)
  };
});

afterEach(() => cleanup());

describe("RunListPage", () => {
  it("renders the v2 workbench layout around the selected run", async () => {
    render(<RunListPage />);

    expect(await screen.findByText("Design Review Workbench")).toBeTruthy();
    expect(await screen.findByLabelText("Stage progress")).toBeTruthy();
    expect(await screen.findByLabelText("Agent conversation")).toBeTruthy();
    expect(await screen.findByLabelText("Execution panel")).toBeTruthy();
    expect(await screen.findByRole("button", { name: "Agent settings" })).toBeTruthy();
    expect((await screen.findAllByText("Codex / GPT-5.5")).length).toBeGreaterThan(0);
    expect(await screen.findByText("Human input required")).toBeTruthy();
  });

  it("saves human action text without requiring JSON", async () => {
    render(<RunListPage />);

    fireEvent.change(await screen.findByLabelText("Human response"), {
      target: { value: "这是我对本阶段问题的自然语言回答。" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Save response" }));

    await waitFor(() => {
      expect(saveClarificationAnswers).toHaveBeenCalledWith("run_1", {
        human_response: "这是我对本阶段问题的自然语言回答。"
      });
    });
  });

  it("opens final output content from the workbench", async () => {
    render(<RunListPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Open Design Doc" }));

    await waitFor(() => {
      expect(readRunFile).toHaveBeenCalledWith("run_1", "output/design_doc.md");
    });
    expect(await screen.findByText("# Design Doc")).toBeTruthy();
    expect(await screen.findByText("Ready.")).toBeTruthy();
  });
});
