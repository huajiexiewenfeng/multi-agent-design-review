import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RunControls } from "../components/RunControls";

afterEach(() => cleanup());

describe("RunControls", () => {
  it("runs one graph step", () => {
    const onRunStep = vi.fn();
    const onFinalize = vi.fn();
    render(<RunControls disabled={false} onRunStep={onRunStep} onFinalize={onFinalize} />);

    fireEvent.click(screen.getByText("Run Graph Step"));

    expect(onRunStep).toHaveBeenCalledOnce();
  });

  it("finalizes output documents", () => {
    const onRunStep = vi.fn();
    const onFinalize = vi.fn();
    render(<RunControls disabled={false} onRunStep={onRunStep} onFinalize={onFinalize} canFinalize />);

    fireEvent.click(screen.getByText("Finalize Output"));

    expect(onFinalize).toHaveBeenCalledOnce();
  });
});
