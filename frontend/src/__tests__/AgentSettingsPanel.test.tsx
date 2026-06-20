import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AgentSettingsPanel } from "../components/AgentSettingsPanel";

afterEach(() => cleanup());

describe("AgentSettingsPanel", () => {
  it("submits CLI runner and model changes", () => {
    const onSave = vi.fn();
    render(
      <AgentSettingsPanel
        agents={[
          {
            id: "architect",
            label: "Architect",
            runner: "mock",
            llm_name: "Mock runner",
            model: "Mock runner",
            stages: ["draft_design"]
          }
        ]}
        onSave={onSave}
      />
    );

    fireEvent.change(screen.getByLabelText("Architect runner"), { target: { value: "claude-code" } });
    fireEvent.change(screen.getByLabelText("Architect model"), { target: { value: "opus" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(onSave).toHaveBeenCalledWith("architect", {
      runner: "claude-code",
      model: "opus"
    });
  });

  it("tests the selected CLI runner and model for an agent", () => {
    const onSmokeTest = vi.fn();
    render(
      <AgentSettingsPanel
        agents={[
          {
            id: "architect",
            label: "Architect",
            runner: "mock",
            llm_name: "Mock runner",
            model: "Mock runner",
            stages: ["draft_design"]
          }
        ]}
        onSave={vi.fn()}
        onSmokeTest={onSmokeTest}
      />
    );

    fireEvent.change(screen.getByLabelText("Architect runner"), { target: { value: "claude-code" } });
    fireEvent.change(screen.getByLabelText("Architect model"), { target: { value: "opus" } });
    fireEvent.click(screen.getByRole("button", { name: "Test model" }));

    expect(onSmokeTest).toHaveBeenCalledWith("architect", {
      runner: "claude-code",
      model: "opus"
    });
  });

  it("uses verified model defaults when switching runners", () => {
    render(
      <AgentSettingsPanel
        agents={[
          {
            id: "architect",
            label: "Architect",
            runner: "mock",
            llm_name: "Mock runner",
            model: "Mock runner",
            stages: ["draft_design"]
          }
        ]}
        onSave={vi.fn()}
      />
    );

    fireEvent.change(screen.getByLabelText("Architect runner"), { target: { value: "claude-code" } });
    expect((screen.getByLabelText("Architect model") as HTMLSelectElement).value).toBe("opus");
    expect(document.querySelector('option[value="claude-opus-4.8"]')).toBeNull();

    fireEvent.change(screen.getByLabelText("Architect runner"), { target: { value: "codex" } });
    expect((screen.getByLabelText("Architect model") as HTMLSelectElement).value).toBe("gpt-5.5");

    fireEvent.change(screen.getByLabelText("Architect runner"), { target: { value: "antigravity" } });
    expect((screen.getByLabelText("Architect model") as HTMLSelectElement).value).toBe("Gemini 3.5 Flash (High)");
  });

  it("replaces stale saved model aliases with the verified runner default", () => {
    render(
      <AgentSettingsPanel
        agents={[
          {
            id: "architect",
            label: "Architect",
            runner: "claude-code",
            llm_name: "claude-sonnet-4.5",
            model: "claude-sonnet-4.5",
            stages: ["draft_design"]
          }
        ]}
        onSave={vi.fn()}
      />
    );

    expect((screen.getByLabelText("Architect model") as HTMLSelectElement).value).toBe("opus");
    expect(document.querySelector('option[value="claude-sonnet-4.5"]')).toBeNull();
  });

  it("does not offer headless model testing for interactive Antigravity", () => {
    const onSmokeTest = vi.fn();
    render(
      <AgentSettingsPanel
        agents={[
          {
            id: "engineer",
            label: "Engineer",
            runner: "antigravity",
            llm_name: "Gemini 3.5 Flash (High)",
            model: "Gemini 3.5 Flash (High)",
            stages: ["draft_design"]
          }
        ]}
        onSave={vi.fn()}
        onSmokeTest={onSmokeTest}
      />
    );

    expect((screen.getByRole("button", { name: "Interactive only" }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Interactive only" }));
    expect(onSmokeTest).not.toHaveBeenCalled();
    expect(screen.getByText("Use handoff; Antigravity opens a trusted workspace.")).toBeTruthy();
  });

  it("shows the model smoke result for an agent", () => {
    render(
      <AgentSettingsPanel
        agents={[
          {
            id: "architect",
            label: "Architect",
            runner: "claude-code",
            llm_name: "opus",
            model: "opus",
            stages: ["draft_design"]
          }
        ]}
        onSave={vi.fn()}
        smokeResults={{
          architect: {
            runner_id: "claude-code",
            model: "opus",
            status: "succeeded",
            exit_code: 0,
            output_content: "MADR_RUNNER_SMOKE_OK",
            log_content: "exit_code: 0",
            error_message: null,
            smoke_dir: "_runner_smoke/claude-code/demo"
          }
        }}
      />
    );

    expect(screen.getByText("succeeded")).toBeTruthy();
    expect(screen.getByText("claude-code / opus")).toBeTruthy();
  });
});
