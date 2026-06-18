import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StageBoard } from "../components/StageBoard";

afterEach(() => cleanup());

describe("StageBoard", () => {
  it("marks current stage", () => {
    render(<StageBoard currentStage="draft_design" missingInputs={["agents/architect/draft_response.v*.md"]} />);
    expect(screen.getByLabelText("Draft Design stage").getAttribute("data-current")).toBe("true");
    expect(screen.getByText("1 missing")).toBeTruthy();
  });

  it("shows each agent llm name", () => {
    render(
      <StageBoard
        currentStage="draft_design"
        agents={[
          {
            id: "architect",
            label: "Architect",
            runner: "claude-code",
            llm_name: "claude-sonnet-4.5",
            stages: ["draft_design"]
          }
        ]}
      />
    );

    const roster = screen.getByLabelText("Agent LLM assignments");
    expect(within(roster).getByText("Architect")).toBeTruthy();
    expect(within(roster).getByText("Claude Code")).toBeTruthy();
    expect(within(roster).getByText("claude-sonnet-4.5")).toBeTruthy();
  });

  it("renders the second-version flow board structure", () => {
    render(<StageBoard currentStage="clarification" />);

    expect(screen.getByLabelText("Flow board")).toBeTruthy();
    expect(screen.getByText("Requirement")).toBeTruthy();
    expect(screen.getByText("Final Output")).toBeTruthy();
  });

  it("selects a stage card", () => {
    const onSelectStage = vi.fn();
    render(<StageBoard currentStage="clarification" onSelectStage={onSelectStage} />);

    screen.getByLabelText("Draft Design stage").click();

    expect(onSelectStage).toHaveBeenCalledWith("draft_design");
  });
});
