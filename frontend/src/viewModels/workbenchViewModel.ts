import type {
  AgentProjection,
  FlowVerification,
  GraphJob,
  RunProjection,
  RunnerHandoff,
  RunnerLog,
  StageArtifact,
  TimelineEvent
} from "../types/run";

type StageState = "complete" | "in_progress" | "blocked" | "pending" | "failed";

export type StageRailItem = {
  id: string;
  label: string;
  state: StageState;
  missingCount: number;
};

export type ConversationMessage = {
  id: string;
  actor: string;
  actorLabel: string;
  actorType: string;
  stage: string | null;
  eventType: string;
  body: string;
  timestamp: string | null;
  relatedFile: string | null;
  runnerLabel: string | null;
  llmName: string | null;
};

export type AgentQueueItem = {
  id: string;
  label: string;
  runnerLabel: string;
  llmName: string;
  status: StageState | "waiting_input";
  task: string;
};

export type HumanActionItem = {
  id: string;
  title: string;
  description: string;
  missingInput: string;
  inputLabel: string;
};

export type WorkbenchArtifact = {
  path: string;
  kind: string;
  agentId: string | null;
};

export type FinalOutputItem = {
  path: string;
  label: string;
  exists: boolean;
  ready: boolean;
};

export type WorkbenchJobStatus = {
  status: GraphJob["status"];
  message: string;
  mode: GraphJob["mode"] | null;
};

export type WorkbenchViewModel = {
  stageRail: StageRailItem[];
  conversation: ConversationMessage[];
  agentQueue: AgentQueueItem[];
  humanActions: HumanActionItem[];
  artifacts: WorkbenchArtifact[];
  finalOutputs: FinalOutputItem[];
  jobStatus: WorkbenchJobStatus | null;
};

export type WorkbenchViewModelInput = {
  run: RunProjection | null;
  events: TimelineEvent[];
  artifacts: StageArtifact[];
  runnerHandoffs: RunnerHandoff[];
  runnerLogs: RunnerLog[];
  flowVerification: FlowVerification | null;
  activeJob: GraphJob | null;
};

const VISIBLE_STAGES = [
  { id: "requirement", label: "Requirement" },
  { id: "clarification", label: "Clarification" },
  { id: "draft_design", label: "Draft" },
  { id: "cross_review", label: "Review" },
  { id: "revision", label: "Revision" },
  { id: "synthesis", label: "Final" }
];

const FINAL_OUTPUTS = [
  { path: "output/design_doc.md", label: "Design Doc" },
  { path: "output/execution_doc.md", label: "Execution Doc" },
  { path: "output/transcript.md", label: "Transcript" }
];

const RUNNER_LABELS: Record<string, string> = {
  mock: "Mock",
  manual: "Manual",
  file: "File Drop",
  codex: "Codex",
  "claude-code": "Claude Code",
  antigravity: "Antigravity"
};

export function buildWorkbenchViewModel(input: WorkbenchViewModelInput): WorkbenchViewModel {
  const agents = input.run?.agents ?? [];
  const artifactsByPath = new Map(input.artifacts.map((artifact) => [artifact.path, artifact]));

  return {
    stageRail: buildStageRail(input.run),
    conversation: buildConversation(input.events, artifactsByPath, agents),
    agentQueue: buildAgentQueue(input.run, agents),
    humanActions: buildHumanActions(input.run),
    artifacts: input.artifacts.map((artifact) => ({
      path: artifact.path,
      kind: artifact.kind,
      agentId: artifact.agent_id
    })),
    finalOutputs: buildFinalOutputs(input.flowVerification),
    jobStatus: input.activeJob
      ? {
          status: input.activeJob.status,
          message: input.activeJob.message,
          mode: input.activeJob.mode ?? null
        }
      : null
  };
}

function buildStageRail(run: RunProjection | null): StageRailItem[] {
  const currentStage = run?.stage ?? "requirement";
  const currentIndex = VISIBLE_STAGES.findIndex((stage) => stage.id === currentStage);

  return VISIBLE_STAGES.map((stage, index) => {
    const isCurrent = stage.id === currentStage;
    const missingCount = isCurrent ? run?.missing_inputs.length ?? 0 : 0;
    return {
      ...stage,
      missingCount,
      state: stageStateFor(run, index, currentIndex, missingCount)
    };
  });
}

function stageStateFor(
  run: RunProjection | null,
  index: number,
  currentIndex: number,
  missingCount: number
): StageState {
  if (!run) {
    return index === 0 ? "in_progress" : "pending";
  }
  if (index < currentIndex) {
    return "complete";
  }
  if (index > currentIndex) {
    return "pending";
  }
  if (run.status === "failed") {
    return "failed";
  }
  if (missingCount > 0 || run.status === "waiting_input") {
    return "blocked";
  }
  return "in_progress";
}

function buildConversation(
  events: TimelineEvent[],
  artifactsByPath: Map<string, StageArtifact>,
  agents: AgentProjection[]
): ConversationMessage[] {
  return events.map((event) => {
    const agent = agents.find((candidate) => candidate.id === event.actor);
    const artifact = event.related_file ? artifactsByPath.get(event.related_file) : null;
    return {
      id: event.id,
      actor: event.actor,
      actorLabel: agent?.label ?? titleCase(event.actor),
      actorType: event.actor_type ?? "agent",
      stage: event.stage ?? null,
      eventType: event.event_type,
      body: artifact?.content ?? event.message,
      timestamp: event.timestamp ?? null,
      relatedFile: event.related_file ?? null,
      runnerLabel: agent ? RUNNER_LABELS[agent.runner] ?? titleCase(agent.runner) : null,
      llmName: agent?.model ?? agent?.llm_name ?? null
    };
  });
}

function buildAgentQueue(run: RunProjection | null, agents: AgentProjection[]): AgentQueueItem[] {
  const currentStage = run?.stage ?? "requirement";
  return agents.map((agent) => {
    const active = agent.stages.includes(currentStage);
    return {
      id: agent.id,
      label: agent.label,
      runnerLabel: RUNNER_LABELS[agent.runner] ?? titleCase(agent.runner),
      llmName: agent.model ?? agent.llm_name,
      status: active ? (run?.missing_inputs.length ? "waiting_input" : "in_progress") : "pending",
      task: active ? `Working on ${stageLabel(currentStage)}` : `Pending ${stageLabel(currentStage)}`
    };
  });
}

function buildHumanActions(run: RunProjection | null): HumanActionItem[] {
  return (run?.missing_inputs ?? []).map((missingInput, index) => ({
    id: `human_action_${index + 1}`,
    title: "Human input required",
    description: missingInputDescription(missingInput),
    missingInput,
    inputLabel: missingInputLabel(missingInput)
  }));
}

function buildFinalOutputs(flowVerification: FlowVerification | null): FinalOutputItem[] {
  return FINAL_OUTPUTS.map((output) => {
    const status = flowVerification?.final_outputs.find((candidate) => candidate.path === output.path);
    return {
      ...output,
      exists: status?.exists ?? false,
      ready: status?.ready ?? false
    };
  });
}

function stageLabel(stageId: string): string {
  return VISIBLE_STAGES.find((stage) => stage.id === stageId)?.label ?? titleCase(stageId);
}

function missingInputDescription(path: string): string {
  if (path.includes("human_answers")) {
    return "Answer the agent questions before the workflow can continue.";
  }
  if (path.includes("final_approval")) {
    return "Approve the synthesized draft before final documents are generated.";
  }
  if (path.includes("clarified_requirement")) {
    return "Confirm the clarified requirement before draft work starts.";
  }
  return `Resolve missing input: ${path}`;
}

function missingInputLabel(path: string): string {
  if (path.includes("human_answers")) {
    return "Human answers";
  }
  if (path.includes("final_approval")) {
    return "Final approval";
  }
  if (path.includes("clarified_requirement")) {
    return "Clarified requirement";
  }
  return path;
}

function titleCase(value: string): string {
  return value
    .split(/[-_ ]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
