import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StageDetailPanel } from "../components/StageDetailPanel";

afterEach(() => cleanup());

describe("StageDetailPanel", () => {
  it("shows selected stage artifacts", () => {
    render(
      <StageDetailPanel
        stage="clarification"
        artifacts={[
          {
            path: "agents/architect/clarification_prompt.md",
            kind: "prompt",
            agent_id: "architect",
            content: "# Prompt\nAsk questions"
          }
        ]}
        missingInputs={["agents/reviewer/clarification_questions.v*.md"]}
        agents={[{ id: "architect", label: "Architect", runner: "mock", llm_name: "Mock runner", stages: ["clarification"] }]}
      />
    );

    expect(screen.getByLabelText("Stage detail")).toBeTruthy();
    expect(screen.getByText("clarification")).toBeTruthy();
    expect(screen.getByText("agents/architect/clarification_prompt.md")).toBeTruthy();
    expect(within(screen.getByText("agents/architect/clarification_prompt.md").closest("article")!).getByText(/Ask questions/)).toBeTruthy();
    expect(screen.getByText("agents/reviewer/clarification_questions.v*.md")).toBeTruthy();
  });

  it("submits pasted agent output for the selected stage", () => {
    const onSubmitOutput = vi.fn();
    render(
      <StageDetailPanel
        stage="clarification"
        artifacts={[]}
        missingInputs={[]}
        agents={[
          {
            id: "architect",
            label: "Architect",
            runner: "mock",
            llm_name: "Mock runner",
            stages: ["clarification"]
          }
        ]}
        onSubmitOutput={onSubmitOutput}
      />
    );

    fireEvent.change(screen.getByLabelText("Output agent"), { target: { value: "architect" } });
    fireEvent.change(screen.getByLabelText("Agent output markdown"), {
      target: { value: "## Clarification Questions\n\n1. [required] Target user?\n\n## Assumptions\n\n- Local." }
    });
    fireEvent.click(screen.getByText("Submit Output"));

    expect(onSubmitOutput).toHaveBeenCalledWith(
      "architect",
      "clarification",
      "## Clarification Questions\n\n1. [required] Target user?\n\n## Assumptions\n\n- Local."
    );
  });

  it("submits human checkpoint inputs for clarified requirement", () => {
    const onSaveAnswers = vi.fn();
    const onSaveRequirement = vi.fn();
    render(
      <StageDetailPanel
        stage="clarified_requirement"
        artifacts={[]}
        missingInputs={[]}
        onSaveAnswers={onSaveAnswers}
        onSaveRequirement={onSaveRequirement}
      />
    );

    fireEvent.change(screen.getByLabelText("Human answers JSON"), { target: { value: '{"q_001":"Local user"}' } });
    fireEvent.click(screen.getByText("Save Answers"));
    fireEvent.change(screen.getByLabelText("Clarified requirement"), { target: { value: "# Clarified\nLocal user MVP." } });
    fireEvent.click(screen.getByText("Save Clarified Requirement"));

    expect(onSaveAnswers).toHaveBeenCalledWith({ q_001: "Local user" });
    expect(onSaveRequirement).toHaveBeenCalledWith("# Clarified\nLocal user MVP.");
  });

  it("skips a blocking agent with a reason", () => {
    const onSkipAgent = vi.fn();
    render(
      <StageDetailPanel
        stage="clarification"
        artifacts={[]}
        missingInputs={["agents/reviewer/clarification_questions.v*.md"]}
        agents={[
          {
            id: "reviewer",
            label: "Reviewer",
            runner: "manual",
            llm_name: "Claude Code",
            stages: ["clarification"]
          }
        ]}
        onSkipAgent={onSkipAgent}
      />
    );

    fireEvent.change(screen.getByLabelText("Skip agent"), { target: { value: "reviewer" } });
    fireEvent.change(screen.getByLabelText("Skip reason"), { target: { value: "Reviewer unavailable for MVP run." } });
    fireEvent.click(screen.getByText("Skip Agent"));

    expect(onSkipAgent).toHaveBeenCalledWith("reviewer", "clarification", "Reviewer unavailable for MVP run.");
  });
});
