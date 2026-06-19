import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { FlowVerificationPanel } from "../components/FlowVerificationPanel";

afterEach(() => cleanup());

describe("FlowVerificationPanel", () => {
  it("shows final output and runner evidence status", () => {
    render(
      <FlowVerificationPanel
        verification={{
          run_id: "run_001",
          complete: true,
          final_outputs_ready: true,
          final_outputs: [
            { path: "output/design_doc.md", exists: true, non_empty: true, ready: true },
            { path: "output/execution_doc.md", exists: true, non_empty: true, ready: true }
          ],
          runners: [
            {
              runner: "codex",
              satisfied: true,
              evidence: [
                {
                  event_id: "evt_1",
                  event_type: "runner_succeeded",
                  stage: "draft_design",
                  agent_id: "architect",
                  message: "codex completed",
                  related_file: "runner_logs/architect/command.log",
                  metadata: {}
                }
              ]
            },
            { runner: "claude-code", satisfied: true, evidence: [] },
            { runner: "antigravity", satisfied: true, evidence: [] }
          ]
        }}
      />
    );

    expect(screen.getByText("Flow Verification")).toBeTruthy();
    expect(screen.getByText("Complete")).toBeTruthy();
    expect(screen.getByText("codex")).toBeTruthy();
    expect(screen.getByText("runner_succeeded")).toBeTruthy();
  });
});
