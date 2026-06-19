export type AgentProjection = {
  id: string;
  label: string;
  runner: string;
  llm_name: string;
  stages: string[];
};

export type RunProjection = {
  run_id: string;
  stage: string;
  status: string;
  missing_inputs: string[];
  current_versions?: Record<string, string>;
  agents?: AgentProjection[];
};

export type TimelineEvent = {
  id: string;
  run_id?: string;
  timestamp?: string;
  stage?: string;
  actor: string;
  actor_type?: string;
  event_type: string;
  message: string;
  related_file?: string | null;
};

export type StageArtifact = {
  path: string;
  kind: string;
  agent_id: string | null;
  content: string;
};

export type GraphJob = {
  id: string;
  run_id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  message: string;
  projection?: RunProjection | null;
  error?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at: string;
};

export type RunnerHealth = {
  id: string;
  label: string;
  available: boolean;
  configured: boolean;
  executable: string | null;
  version: string | null;
  env: string;
  command_template: string | null;
  error: string | null;
};
