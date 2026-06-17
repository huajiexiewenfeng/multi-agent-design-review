import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { HumanInputPanel } from "../components/HumanInputPanel";

describe("HumanInputPanel", () => {
  it("submits clarification answers and clarified requirement", () => {
    const onSaveAnswers = vi.fn();
    const onSaveRequirement = vi.fn();
    render(<HumanInputPanel onSaveAnswers={onSaveAnswers} onSaveRequirement={onSaveRequirement} />);

    fireEvent.change(screen.getByLabelText("Human answers JSON"), { target: { value: '{"q_001":"Local developer"}' } });
    fireEvent.click(screen.getByText("Save Answers"));
    fireEvent.change(screen.getByLabelText("Clarified requirement"), { target: { value: "# Clarified" } });
    fireEvent.click(screen.getByText("Save Clarified Requirement"));

    expect(onSaveAnswers).toHaveBeenCalledWith({ q_001: "Local developer" });
    expect(onSaveRequirement).toHaveBeenCalledWith("# Clarified");
  });
});
