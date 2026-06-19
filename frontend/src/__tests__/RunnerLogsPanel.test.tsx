import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RunnerLogsPanel } from "../components/RunnerLogsPanel";

describe("RunnerLogsPanel", () => {
  it("shows runner command logs", () => {
    render(
      <RunnerLogsPanel
        logs={[
          {
            agent_id: "architect",
            path: "runner_logs/architect/command.log",
            content: "exit_code: 1"
          }
        ]}
      />
    );

    expect(screen.getByText("architect")).toBeTruthy();
    expect(screen.getByText("runner_logs/architect/command.log")).toBeTruthy();
    expect(screen.getByText(/exit_code: 1/)).toBeTruthy();
  });
});
