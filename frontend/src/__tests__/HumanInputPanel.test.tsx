import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { HumanInputPanel } from "../components/HumanInputPanel";

afterEach(() => cleanup());

describe("HumanInputPanel", () => {
  it("submits natural-language clarification answers and clarified requirement", () => {
    const onSaveAnswers = vi.fn();
    const onSaveRequirement = vi.fn();
    render(<HumanInputPanel onSaveAnswers={onSaveAnswers} onSaveRequirement={onSaveRequirement} />);

    fireEvent.change(screen.getByLabelText("Human answers"), { target: { value: "Local developer using Web UI." } });
    fireEvent.click(screen.getByText("Save Answers"));
    fireEvent.change(screen.getByLabelText("Clarified requirement"), { target: { value: "# Clarified" } });
    fireEvent.click(screen.getByText("Save Clarified Requirement"));

    expect(onSaveAnswers).toHaveBeenCalledWith("Local developer using Web UI.");
    expect(onSaveRequirement).toHaveBeenCalledWith("# Clarified");
  });

  it("does not expose JSON wording for human answers", () => {
    render(<HumanInputPanel onSaveAnswers={vi.fn()} onSaveRequirement={vi.fn()} />);

    expect(screen.queryByText("Human answers JSON")).toBeNull();
    expect(screen.queryByLabelText("Human answers JSON")).toBeNull();
  });
});
