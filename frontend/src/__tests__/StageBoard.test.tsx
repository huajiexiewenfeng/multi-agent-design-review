import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StageBoard } from "../components/StageBoard";

describe("StageBoard", () => {
  it("marks current stage", () => {
    render(<StageBoard currentStage="draft_design" />);
    expect(screen.getByText("Draft Design").getAttribute("data-current")).toBe("true");
  });
});
