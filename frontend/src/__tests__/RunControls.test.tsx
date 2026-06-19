import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RunControls } from "../components/RunControls";

afterEach(() => cleanup());

describe("RunControls", () => {
  it("runs one graph step", () => {
    const onRunStep = vi.fn();
    const onRunUntilPause = vi.fn();
    const onFinalize = vi.fn();
    render(
      <RunControls
        disabled={false}
        onRunStep={onRunStep}
        onRunUntilPause={onRunUntilPause}
        onFinalize={onFinalize}
      />
    );

    fireEvent.click(screen.getByText("Run Graph Step"));

    expect(onRunStep).toHaveBeenCalledOnce();
  });

  it("runs until a pause point", () => {
    const onRunStep = vi.fn();
    const onRunUntilPause = vi.fn();
    const onFinalize = vi.fn();
    render(
      <RunControls
        disabled={false}
        onRunStep={onRunStep}
        onRunUntilPause={onRunUntilPause}
        onFinalize={onFinalize}
      />
    );

    fireEvent.click(screen.getByText("Run Until Pause"));

    expect(onRunUntilPause).toHaveBeenCalledOnce();
  });

  it("finalizes output documents", () => {
    const onRunStep = vi.fn();
    const onRunUntilPause = vi.fn();
    const onFinalize = vi.fn();
    render(
      <RunControls
        disabled={false}
        onRunStep={onRunStep}
        onRunUntilPause={onRunUntilPause}
        onFinalize={onFinalize}
        canFinalize
      />
    );

    fireEvent.click(screen.getByText("Finalize Output"));

    expect(onFinalize).toHaveBeenCalledOnce();
  });

  it("shows running state while a graph job is active", () => {
    const onRunStep = vi.fn();
    const onRunUntilPause = vi.fn();
    const onFinalize = vi.fn();
    render(
      <RunControls
        disabled={false}
        isRunning
        onRunStep={onRunStep}
        onRunUntilPause={onRunUntilPause}
        onFinalize={onFinalize}
        canFinalize
      />
    );

    fireEvent.click(screen.getByText("Running..."));
    fireEvent.click(screen.getByText("Run Until Pause"));
    fireEvent.click(screen.getByText("Finalize Output"));

    expect(onRunStep).not.toHaveBeenCalled();
    expect(onRunUntilPause).not.toHaveBeenCalled();
    expect(onFinalize).not.toHaveBeenCalled();
  });
});
