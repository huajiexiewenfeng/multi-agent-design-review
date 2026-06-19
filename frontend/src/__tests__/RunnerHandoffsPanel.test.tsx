import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RunnerHandoffsPanel } from "../components/RunnerHandoffsPanel";

describe("RunnerHandoffsPanel", () => {
  it("shows waiting handoffs and can check outputs", () => {
    const onImport = vi.fn();
    render(
      <RunnerHandoffsPanel
        handoffs={[
          {
            event_id: "evt_1",
            agent_id: "architect",
            stage: "clarification",
            message: "Antigravity launched; waiting for output file",
            related_file: "runner_logs/architect/antigravity.log",
            instruction_file: "runner_logs/architect/antigravity_instruction.md",
            instruction: "OUTPUT_FILE: C:/run/inbox/architect/clarification_result.md",
            output_file: "C:/run/inbox/architect/clarification_result.md",
            metadata: { runner: "antigravity" }
          }
        ]}
        onImport={onImport}
      />
    );

    expect(screen.getByText("architect")).toBeTruthy();
    expect(screen.getByText("C:/run/inbox/architect/clarification_result.md")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Check Outputs" }));
    expect(onImport).toHaveBeenCalled();
  });
});
