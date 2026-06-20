import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  approveFinalOutput,
  getRun,
  getStageArtifacts,
  listRuns,
  readRunFile,
  requestDiscussionChanges,
  saveClarificationAnswers,
  startRunnerSmokeJob,
  submitAgentOutput
} from "../api/client";
import { RunListPage } from "../pages/RunListPage";

vi.mock("../api/client", () => {
  const run = {
    run_id: "run_1",
    title: "Checkout redesign",
    stage: "draft_design",
    status: "waiting_input",
    missing_inputs: ["input/human_answers.md"],
    agents: [
      {
        id: "architect",
        label: "Architect",
        runner: "codex",
        llm_name: "GPT-5.5",
        model: "gpt-5.5",
        stages: ["draft_design"]
      }
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
    readRunFile: vi.fn().mockImplementation((_runId: string, path: string) =>
      Promise.resolve({
        path,
        content:
          path === "agents/architect/draft_response.v1.md"
            ? "## Proposed Design\nA v2 workbench"
            : "# Design Doc\n\nReady."
      })
    ),
    saveClarificationAnswers: vi.fn().mockResolvedValue(run),
    saveClarifiedRequirement: vi.fn().mockResolvedValue(run),
    approveFinalOutput: vi.fn().mockResolvedValue(run),
    requestDiscussionChanges: vi.fn().mockResolvedValue(run),
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
    expect(await screen.findByText("Checkout redesign")).toBeTruthy();
    expect((await screen.findAllByText("Codex / gpt-5.5")).length).toBeGreaterThan(0);
    expect(await screen.findByText("Human input required")).toBeTruthy();
  });

  it("saves human action text without requiring JSON", async () => {
    render(<RunListPage />);

    fireEvent.change(await screen.findByLabelText("Human response"), {
      target: { value: "Use natural language from the Web UI." }
    });
    fireEvent.click(screen.getByRole("button", { name: "Save response" }));

    await waitFor(() => {
      expect(saveClarificationAnswers).toHaveBeenCalledWith("run_1", "Use natural language from the Web UI.");
    });
  });

  it("shows a readable error when saving human answers fails", async () => {
    vi.mocked(saveClarificationAnswers).mockRejectedValueOnce(new Error("network offline"));
    render(<RunListPage />);

    fireEvent.change(await screen.findByLabelText("Human response"), {
      target: { value: "Use Codex and Claude Code from the Web UI." }
    });
    fireEvent.click(screen.getByRole("button", { name: "Save response" }));

    expect(await screen.findByText("Save human answers failed: network offline")).toBeTruthy();
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

  it("opens conversation attachments in the central stream", async () => {
    render(<RunListPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Open agents/architect/draft_response.v1.md" }));

    await waitFor(() => {
      expect(readRunFile).toHaveBeenCalledWith("run_1", "agents/architect/draft_response.v1.md");
    });
    const preview = await screen.findByLabelText("agents/architect/draft_response.v1.md preview");
    expect(within(preview).getByText("## Proposed Design")).toBeTruthy();
    expect(within(preview).getByText("A v2 workbench")).toBeTruthy();
  });

  it("starts a model-aware smoke test from agent settings", async () => {
    vi.mocked(startRunnerSmokeJob).mockResolvedValue({
      id: "smoke_job_1",
      runner_id: "claude-code",
      model: "opus",
      status: "queued",
      message: "Runner smoke test queued",
      result: null,
      error: null,
      created_at: "2026-06-19T00:00:00+00:00"
    });
    render(<RunListPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Agent settings" }));
    fireEvent.change(screen.getByLabelText("Architect runner"), { target: { value: "claude-code" } });
    fireEvent.change(screen.getByLabelText("Architect model"), { target: { value: "opus" } });
    fireEvent.click(screen.getByRole("button", { name: "Test model" }));

    await waitFor(() => {
      expect(startRunnerSmokeJob).toHaveBeenCalledWith("claude-code", "opus");
    });
  });

  it("refreshes stage artifacts from the updated run stage after a successful agent submit", async () => {
    const updatedRun = {
      run_id: "run_1",
      title: "Checkout redesign",
      stage: "cross_review",
      status: "waiting_input",
      missing_inputs: ["agents/reviewer/review_response.v*.md"],
      agents: [
        {
          id: "architect",
          label: "Architect",
          runner: "codex",
          llm_name: "GPT-5.5",
          model: "gpt-5.5",
          stages: ["draft_design", "cross_review"]
        }
      ]
    };
    vi.mocked(submitAgentOutput).mockResolvedValueOnce({ related_file: "agents/architect/draft_response.v2.md" });
    vi.mocked(getRun).mockResolvedValueOnce(updatedRun);
    render(<RunListPage />);

    fireEvent.change(await screen.findByLabelText("Agent output markdown"), {
      target: { value: "## Proposed Design\nUpdated draft." }
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit Output" }));

    await waitFor(() => {
      expect(getStageArtifacts).toHaveBeenLastCalledWith("run_1", "cross_review");
    });
  });

  it("routes final approval and change requests to the final discussion APIs", async () => {
    const finalRun = {
      run_id: "run_1",
      title: "Checkout redesign",
      stage: "synthesis",
      status: "waiting_input",
      missing_inputs: ["input/final_approval.md"],
      agents: []
    };
    vi.mocked(getRun).mockResolvedValue(finalRun);
    vi.mocked(listRuns).mockResolvedValueOnce([finalRun]);
    vi.mocked(getStageArtifacts).mockResolvedValue([]);
    render(<RunListPage />);

    fireEvent.change(await screen.findByLabelText("Human response"), {
      target: { value: "Approved. Generate the final docs." }
    });
    fireEvent.click(screen.getByRole("button", { name: "Save response" }));

    await waitFor(() => {
      expect(approveFinalOutput).toHaveBeenCalledWith("run_1", "Approved. Generate the final docs.");
    });

    fireEvent.change(screen.getByLabelText("Request changes"), {
      target: { value: "Please continue discussion on risk handling." }
    });
    fireEvent.click(screen.getByRole("button", { name: "Request changes" }));

    await waitFor(() => {
      expect(requestDiscussionChanges).toHaveBeenCalledWith("run_1", "Please continue discussion on risk handling.");
    });
  });
});
