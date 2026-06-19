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
  mode?: "step" | "until_pause";
  stop_reason?: string | null;
  steps_run?: number;
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

export type RunnerLog = {
  agent_id: string;
  path: string;
  content: string;
};

export type RunnerHandoff = {
  event_id: string;
  agent_id: string;
  stage: string;
  message: string;
  related_file: string | null;
  instruction_file: string | null;
  instruction: string;
  output_file: string;
  metadata: Record<string, unknown>;
};

export type RunnerHandoffImportResult = {
  projection: RunProjection;
  imported: string[];
  errors: Array<{ agent_id: string; stage: string; error: string }>;
};

export type RunnerSmokeResult = {
  runner_id: string;
  status: "succeeded" | "failed";
  exit_code: number | null;
  output_content: string;
  log_content: string;
  error_message: string | null;
  smoke_dir: string;
};

export type RunnerSmokeJob = {
  id: string;
  runner_id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  message: string;
  result?: RunnerSmokeResult | null;
  error?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at: string;
};

export type FlowVerificationEvidence = {
  event_id: string;
  event_type: string;
  stage: string;
  agent_id: string;
  message: string;
  related_file: string | null;
  metadata: Record<string, unknown>;
};

export type FlowVerificationRunner = {
  runner: string;
  satisfied: boolean;
  evidence: FlowVerificationEvidence[];
};

export type FlowVerificationOutput = {
  path: string;
  exists: boolean;
  non_empty: boolean;
  ready: boolean;
};

export type FlowVerification = {
  run_id: string;
  complete: boolean;
  final_outputs_ready: boolean;
  final_outputs: FlowVerificationOutput[];
  runners: FlowVerificationRunner[];
};
