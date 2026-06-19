import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
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
});
