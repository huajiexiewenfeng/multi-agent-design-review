import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AgentSettingsPanel } from "../components/AgentSettingsPanel";

afterEach(() => cleanup());

describe("AgentSettingsPanel", () => {
  it("submits runner and llm name changes", () => {
    const onSave = vi.fn();
    render(
      <AgentSettingsPanel
        agents={[
          {
            id: "architect",
            label: "Architect",
            runner: "mock",
            llm_name: "Mock runner",
            stages: ["draft_design"]
          }
        ]}
        onSave={onSave}
      />
    );

    fireEvent.change(screen.getByLabelText("Architect runner"), { target: { value: "claude-code" } });
    fireEvent.change(screen.getByLabelText("Architect LLM name"), { target: { value: "claude-sonnet-4.5" } });
    fireEvent.click(screen.getByText("Save Architect"));

    expect(onSave).toHaveBeenCalledWith("architect", {
      runner: "claude-code",
      llm_name: "claude-sonnet-4.5"
    });
  });
});
