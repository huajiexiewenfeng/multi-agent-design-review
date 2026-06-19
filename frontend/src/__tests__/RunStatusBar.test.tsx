import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { RunStatusBar } from "../components/RunStatusBar";

afterEach(() => cleanup());

describe("RunStatusBar", () => {
  it("shows active job state and message", () => {
    render(
      <RunStatusBar
        currentStageLabel="Draft"
        humanActionCount={0}
        statusMessage="Running architect"
        jobStatus={{ status: "running", message: "Calling Codex runner", mode: "until_pause" }}
      />
    );

    expect(screen.getByLabelText("Run status")).toBeTruthy();
    expect(screen.getByText("Draft")).toBeTruthy();
    expect(screen.getByText("Running")).toBeTruthy();
    expect(screen.getByText("Calling Codex runner")).toBeTruthy();
  });

  it("makes human waiting state explicit", () => {
    render(
      <RunStatusBar
        currentStageLabel="Review"
        humanActionCount={2}
        statusMessage="Paused: human_input"
        jobStatus={null}
      />
    );

    expect(screen.getByText("Waiting for human")).toBeTruthy();
    expect(screen.getByText("2 actions required")).toBeTruthy();
  });
});
