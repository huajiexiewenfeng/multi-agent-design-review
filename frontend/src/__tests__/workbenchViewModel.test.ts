import { describe, expect, it } from "vitest";
import { buildWorkbenchViewModel } from "../viewModels/workbenchViewModel";

describe("buildWorkbenchViewModel", () => {
  it("maps the current stage into a compact stage rail", () => {
    const viewModel = buildWorkbenchViewModel({
      run: {
        run_id: "run_1",
        stage: "draft_design",
        status: "waiting_input",
        missing_inputs: ["agents/reviewer/review_response.v*.md"],
        agents: []
      },
      events: [],
      artifacts: [],
      runnerHandoffs: [],
      runnerLogs: [],
      flowVerification: null,
      activeJob: null
    });

    expect(viewModel.stageRail.map((stage) => stage.label)).toEqual([
      "Requirement",
      "Clarification",
      "Draft",
      "Review",
      "Revision",
      "Final"
    ]);
    expect(viewModel.stageRail.find((stage) => stage.id === "draft_design")?.state).toBe("blocked");
  });

  it("turns agent output events and artifacts into conversation messages with model names", () => {
    const viewModel = buildWorkbenchViewModel({
      run: {
        run_id: "run_1",
        stage: "draft_design",
        status: "in_progress",
        missing_inputs: [],
        agents: [
          { id: "architect", label: "Architect", runner: "codex", llm_name: "GPT-5.5", stages: ["draft_design"] }
        ]
      },
      events: [
        {
          id: "evt_1",
          actor: "architect",
          actor_type: "agent",
          event_type: "agent_output_submitted",
          message: "Draft submitted",
          stage: "draft_design",
          related_file: "agents/architect/draft_response.v1.md",
          timestamp: "2026-06-19T10:00:00Z"
        }
      ],
      artifacts: [
        {
          path: "agents/architect/draft_response.v1.md",
          kind: "output",
          agent_id: "architect",
          content: "## Proposed Design\nArchitectural plan"
        }
      ],
      runnerHandoffs: [],
      runnerLogs: [],
      flowVerification: null,
      activeJob: null
    });

    expect(viewModel.conversation[0]).toMatchObject({
      actorLabel: "Architect",
      runnerLabel: "Codex",
      llmName: "GPT-5.5",
      body: "## Proposed Design\nArchitectural plan"
    });
  });

  it("exposes human action cards and final output readiness", () => {
    const viewModel = buildWorkbenchViewModel({
      run: {
        run_id: "run_1",
        stage: "synthesis",
        status: "ready_to_advance",
        missing_inputs: ["input/human_answers.json"],
        agents: []
      },
      events: [],
      artifacts: [],
      runnerHandoffs: [],
      runnerLogs: [],
      flowVerification: {
        run_id: "run_1",
        complete: false,
        final_outputs_ready: true,
        final_outputs: [
          { path: "output/design_doc.md", exists: true, non_empty: true, ready: true },
          { path: "output/execution_doc.md", exists: true, non_empty: true, ready: true }
        ],
        runners: []
      },
      activeJob: null
    });

    expect(viewModel.humanActions[0].title).toContain("Human input required");
    expect(viewModel.finalOutputs.map((output) => output.path)).toEqual([
      "output/design_doc.md",
      "output/execution_doc.md",
      "output/transcript.md"
    ]);
    expect(viewModel.finalOutputs[0].ready).toBe(true);
    expect(viewModel.finalOutputs[2].ready).toBe(false);
  });
});
