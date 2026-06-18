import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { Timeline } from "../components/Timeline";

afterEach(() => cleanup());

describe("Timeline", () => {
  it("renders events as a discussion timeline", () => {
    render(
      <Timeline
        events={[
          {
            id: "evt_1",
            actor: "architect",
            actor_type: "agent",
            event_type: "prompt_generated",
            message: "Architect prompt generated",
            stage: "clarification",
            timestamp: "2026-06-18T10:00:00Z"
          }
        ]}
      />
    );

    expect(screen.getByLabelText("Discussion timeline")).toBeTruthy();
    expect(screen.getByText("architect")).toBeTruthy();
    expect(screen.getByText("prompt_generated")).toBeTruthy();
    expect(screen.getByText("Architect prompt generated")).toBeTruthy();
  });
});
