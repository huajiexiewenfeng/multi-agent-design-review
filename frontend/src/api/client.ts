import type {
  FlowVerification,
  GraphJob,
  RunnerHandoff,
  RunnerHandoffImportResult,
  RunnerHealth,
  RunnerLog,
  RunnerSmokeJob,
  RunnerSmokeResult,
  RunProjection,
  StageArtifact,
  TimelineEvent
} from "../types/run";

export async function listRuns(): Promise<RunProjection[]> {
  const response = await fetch("/api/runs");
  return response.json();
}

export async function getRunners(): Promise<RunnerHealth[]> {
  const response = await fetch("/api/runners");
  if (!response.ok) {
    throw new Error(`Failed to load runners: ${response.status}`);
  }
  return response.json();
}

export async function runRunnerSmokeTest(runnerId: string): Promise<RunnerSmokeResult> {
  const response = await fetch(`/api/runners/${runnerId}/smoke-test`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Failed to run runner smoke test: ${response.status}`);
  }
  return response.json();
}

export async function startRunnerSmokeJob(runnerId: string): Promise<RunnerSmokeJob> {
  const response = await fetch(`/api/runners/${runnerId}/smoke-test/jobs`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Failed to start runner smoke job: ${response.status}`);
  }
  return response.json();
}

export async function getRunnerSmokeJob(runnerId: string, jobId: string): Promise<RunnerSmokeJob> {
  const response = await fetch(`/api/runners/${runnerId}/smoke-test/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error(`Failed to load runner smoke job: ${response.status}`);
  }
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

export async function getRun(runId: string): Promise<RunProjection> {
  const response = await fetch(`/api/runs/${runId}`);
  return response.json();
}

export async function getEvents(runId: string): Promise<TimelineEvent[]> {
  const response = await fetch(`/api/runs/${runId}/events`);
  return response.json();
}

export async function getRunnerLogs(runId: string): Promise<RunnerLog[]> {
  const response = await fetch(`/api/runs/${runId}/runner-logs`);
  if (!response.ok) {
    throw new Error(`Failed to load runner logs: ${response.status}`);
  }
  const body = await response.json();
  return body.logs;
}

export async function getRunnerHandoffs(runId: string): Promise<RunnerHandoff[]> {
  const response = await fetch(`/api/runs/${runId}/runner-handoffs`);
  if (!response.ok) {
    throw new Error(`Failed to load runner handoffs: ${response.status}`);
  }
  const body = await response.json();
  return body.handoffs;
}

export async function importRunnerHandoffs(runId: string): Promise<RunnerHandoffImportResult> {
  const response = await fetch(`/api/runs/${runId}/runner-handoffs/import`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Failed to import runner handoffs: ${response.status}`);
  }
  return response.json();
}

export async function getFlowVerification(runId: string): Promise<FlowVerification> {
  const response = await fetch(`/api/runs/${runId}/verification/mixed-runners`);
  if (!response.ok) {
    throw new Error(`Failed to load flow verification: ${response.status}`);
  }
  return response.json();
}

export async function getStageArtifacts(runId: string, stage: string): Promise<StageArtifact[]> {
  const response = await fetch(`/api/runs/${runId}/stages/${stage}/artifacts`);
  if (!response.ok) {
    throw new Error(`Failed to load stage artifacts: ${response.status}`);
  }
  const body = await response.json();
  return body.artifacts;
}

export async function updateAgentConfig(
  runId: string,
  agentId: string,
  runner: string,
  llmName: string,
): Promise<RunProjection> {
  const response = await fetch(`/api/runs/${runId}/agents/${agentId}/config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ runner, llm_name: llmName })
  });
  if (!response.ok) {
    throw new Error(`Failed to update agent config: ${response.status}`);
  }
  return response.json();
}

export async function runGraphStep(runId: string, confirmed = true): Promise<RunProjection> {
  const response = await fetch(`/api/runs/${runId}/graph/step`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirmed })
  });
  if (!response.ok) {
    throw new Error(`Failed to run graph step: ${response.status}`);
  }
  const body = await response.json();
  return body.projection;
}

export async function startGraphStepJob(runId: string, confirmed = true): Promise<GraphJob> {
  const response = await fetch(`/api/runs/${runId}/graph/step/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirmed })
  });
  if (!response.ok) {
    throw new Error(`Failed to start graph job: ${response.status}`);
  }
  return response.json();
}

export async function startRunUntilPauseJob(runId: string, maxSteps = 10): Promise<GraphJob> {
  const response = await fetch(`/api/runs/${runId}/graph/until-pause/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ max_steps: maxSteps })
  });
  if (!response.ok) {
    throw new Error(`Failed to start run-until-pause job: ${response.status}`);
  }
  return response.json();
}

export async function getGraphJob(runId: string, jobId: string): Promise<GraphJob> {
  const response = await fetch(`/api/runs/${runId}/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error(`Failed to load graph job: ${response.status}`);
  }
  return response.json();
}

export async function finalizeRun(runId: string): Promise<RunProjection> {
  const response = await fetch(`/api/runs/${runId}/finalize`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error(`Failed to finalize run: ${response.status}`);
  }
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
  if (!response.ok) {
    throw new Error(`Failed to submit agent output: ${response.status}`);
  }
  return response.json();
}

export async function saveClarificationAnswers(runId: string, answers: Record<string, string>): Promise<RunProjection> {
  const response = await fetch(`/api/runs/${runId}/clarification/answers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers })
  });
  if (!response.ok) {
    throw new Error(`Failed to save clarification answers: ${response.status}`);
  }
  return response.json();
}

export async function saveClarifiedRequirement(runId: string, content: string): Promise<RunProjection> {
  const response = await fetch(`/api/runs/${runId}/clarified-requirement`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content })
  });
  if (!response.ok) {
    throw new Error(`Failed to save clarified requirement: ${response.status}`);
  }
  return response.json();
}

export async function skipAgent(
  runId: string,
  agentId: string,
  stage: string,
  reason: string,
): Promise<RunProjection> {
  const response = await fetch(`/api/runs/${runId}/agents/${agentId}/skip`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stage, reason })
  });
  if (!response.ok) {
    throw new Error(`Failed to skip agent: ${response.status}`);
  }
  return response.json();
}
