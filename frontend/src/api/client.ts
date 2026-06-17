import type { RunProjection, TimelineEvent } from "../types/run";

export async function listRuns(): Promise<RunProjection[]> {
  const response = await fetch("/api/runs");
  return response.json();
}

export async function createRun(title: string, requirement: string): Promise<RunProjection> {
  const response = await fetch("/api/runs", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ title, requirement })
  });
  if (!response.ok) {
    throw new Error(`Failed to create run: ${response.status}`);
  }
  return response.json();
}

export async function getEvents(runId: string): Promise<TimelineEvent[]> {
  const response = await fetch(`/api/runs/${runId}/events`);
  return response.json();
}

export async function submitAgentOutput(
  runId: string,
  agentId: string,
  stage: string,
  content: string,
): Promise<{ related_file: string }> {
  const response = await fetch(`/api/runs/${runId}/agents/${agentId}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stage, content })
  });
  return response.json();
}
