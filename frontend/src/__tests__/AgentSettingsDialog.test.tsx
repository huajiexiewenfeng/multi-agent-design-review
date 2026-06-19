import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AgentSettingsDialog } from "../components/AgentSettingsDialog";
import type { AgentProjection } from "../types/run";

afterEach(() => cleanup());

const agents: AgentProjection[] = [
  {
    id: "architect",
    label: "Architect",
    runner: "codex",
    llm_name: "GPT-5.5",
    stages: ["clarification", "draft_design"]
  }
];

describe("AgentSettingsDialog", () => {
  it("opens agent model settings in a dialog and saves changes", () => {
    const onSave = vi.fn();
    render(<AgentSettingsDialog agents={agents} onSave={onSave} />);

    fireEvent.click(screen.getByRole("button", { name: "Agent settings" }));

    expect(screen.getByRole("dialog", { name: "Agent settings" })).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Architect runner"), { target: { value: "claude-code" } });
    fireEvent.change(screen.getByLabelText("Architect LLM name"), { target: { value: "claude opus 4.8" } });
    fireEvent.click(screen.getByRole("button", { name: "Save Architect" }));

    expect(onSave).toHaveBeenCalledWith("architect", {
      runner: "claude-code",
      llm_name: "claude opus 4.8"
    });
  });
});
