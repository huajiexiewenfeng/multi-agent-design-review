import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SubmitOutputDialog } from "../components/SubmitOutputDialog";

describe("SubmitOutputDialog", () => {
  it("submits pasted output", () => {
    const onSubmit = vi.fn();
    render(<SubmitOutputDialog agentId="architect" stage="draft_design" onSubmit={onSubmit} />);
    fireEvent.change(screen.getByLabelText("Agent output"), { target: { value: "## Summary\nA" } });
    fireEvent.click(screen.getByText("Submit"));
    expect(onSubmit).toHaveBeenCalledWith("architect", "draft_design", "## Summary\nA");
  });
});
