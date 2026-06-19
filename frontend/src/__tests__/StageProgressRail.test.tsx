import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StageProgressRail } from "../components/StageProgressRail";
import type { StageRailItem } from "../viewModels/workbenchViewModel";

afterEach(() => cleanup());

const stages: StageRailItem[] = [
  { id: "requirement", label: "Requirement", state: "complete", missingCount: 0 },
  { id: "clarification", label: "Clarification", state: "complete", missingCount: 0 },
  { id: "draft_design", label: "Draft", state: "blocked", missingCount: 2 },
  { id: "cross_review", label: "Review", state: "pending", missingCount: 0 },
  { id: "revision", label: "Revision", state: "pending", missingCount: 0 },
  { id: "synthesis", label: "Final", state: "pending", missingCount: 0 }
];

describe("StageProgressRail", () => {
  it("renders compact workflow progress and blocked state", () => {
    render(<StageProgressRail stages={stages} selectedStage="draft_design" />);

    expect(screen.getByLabelText("Stage progress")).toBeTruthy();
    expect(screen.getByText("Requirement")).toBeTruthy();
    expect(screen.getByText("Draft")).toBeTruthy();
    expect(screen.getByText("Blocked")).toBeTruthy();
    expect(screen.getByText("2 missing inputs")).toBeTruthy();
  });

  it("selects a stage from the rail", () => {
    const onSelectStage = vi.fn();
    render(<StageProgressRail stages={stages} selectedStage="draft_design" onSelectStage={onSelectStage} />);

    fireEvent.click(screen.getByRole("button", { name: /Review stage/i }));

    expect(onSelectStage).toHaveBeenCalledWith("cross_review");
  });
});
