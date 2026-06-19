import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RunnerHealthPanel } from "../components/RunnerHealthPanel";

describe("RunnerHealthPanel", () => {
  it("shows CLI availability and command template", () => {
    render(
      <RunnerHealthPanel
        runners={[
          {
            id: "codex",
            label: "Codex CLI",
            available: true,
            configured: true,
            executable: "C:/npm/codex.cmd",
            version: "codex-cli 0.141.0",
            env: "MADR_CODEX_COMMAND",
            command_template: "codex {prompt_file}",
            error: null
          }
        ]}
      />
    );

    expect(screen.getByText("Codex CLI")).toBeTruthy();
    expect(screen.getByText("available")).toBeTruthy();
    expect(screen.getByText("codex-cli 0.141.0")).toBeTruthy();
    expect(screen.getByText("codex {prompt_file}")).toBeTruthy();
  });

  it("can request a runner smoke test and show the result", () => {
    const onSmokeTest = vi.fn();
    render(
      <RunnerHealthPanel
        runners={[
          {
            id: "codex",
            label: "Codex CLI",
            available: true,
            configured: true,
            executable: "C:/npm/codex.cmd",
            version: "codex-cli 0.141.0",
            env: "MADR_CODEX_COMMAND",
            command_template: "codex {prompt_file}",
            error: null
          }
        ]}
        onSmokeTest={onSmokeTest}
        smokeResults={{
          codex: {
            runner_id: "codex",
            status: "succeeded",
            exit_code: 0,
            output_content: "MADR_RUNNER_SMOKE_OK",
            log_content: "exit_code: 0",
            error_message: null,
            smoke_dir: "_runner_smoke/codex/demo"
          }
        }}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Test Codex CLI" }));

    expect(onSmokeTest).toHaveBeenCalledWith("codex");
    expect(screen.getByText("succeeded")).toBeTruthy();
    expect(screen.getByText("MADR_RUNNER_SMOKE_OK")).toBeTruthy();
  });
});
