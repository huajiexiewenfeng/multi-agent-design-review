import type { AgentProjection } from "../types/run";

const STAGES = [
  ["requirement", "Requirement", "Capture the raw request"],
  ["clarification", "Clarification", "Agents ask questions"],
  ["clarified_requirement", "Clarified Requirement", "Human confirms scope"],
  ["draft_design", "Draft Design", "Architect and Engineer draft"],
  ["cross_review", "Cross Review", "Reviewer checks conflicts"],
  ["revision", "Revision", "Design is tightened"],
  ["synthesis", "Final Output", "Synthesizer produces docs"]
];

const DEFAULT_AGENTS: AgentProjection[] = [
  {
    id: "architect",
    label: "Architect",
    runner: "mock",
    llm_name: "Mock runner",
    stages: ["clarification", "draft_design", "cross_review", "revision"]
  },
  {
    id: "engineer",
    label: "Engineer",
    runner: "mock",
    llm_name: "Mock runner",
    stages: ["clarification", "draft_design", "cross_review", "revision"]
  },
  {
    id: "reviewer",
    label: "Reviewer",
    runner: "mock",
    llm_name: "Mock runner",
    stages: ["clarification", "cross_review"]
  },
  {
    id: "synthesizer",
    label: "Synthesizer",
    runner: "mock",
    llm_name: "Mock runner",
    stages: ["synthesis"]
  }
];

const RUNNER_LABELS: Record<string, string> = {
  mock: "Mock",
  manual: "Manual",
  file: "File Drop",
  codex: "Codex",
  "claude-code": "Claude Code",
  antigravity: "Antigravity"
};

export function StageBoard({
  currentStage,
  agents = DEFAULT_AGENTS,
  missingInputs = [],
  selectedStage = currentStage,
  onSelectStage
}: {
  currentStage: string;
  agents?: AgentProjection[];
  missingInputs?: string[];
  selectedStage?: string;
  onSelectStage?: (stage: string) => void;
}) {
  return (
    <section className="stage-board" aria-label="Flow board">
      <div className="section-heading">
        <h2>Flow Board</h2>
        <p>Open a stage to inspect its prompts, outputs, and blocked inputs.</p>
      </div>
      <div className="stage-lanes" aria-label="Workflow stages">
        {STAGES.map(([id, label, description]) => {
          const stageAgents = agents.filter((agent) => agent.stages.includes(id));
          const missingCount = id === currentStage ? missingInputs.length : 0;
          return (
            <article
              className="stage-card"
              key={id}
              aria-label={`${label} stage`}
              role="button"
              tabIndex={0}
              data-current={id === currentStage ? "true" : "false"}
              data-selected={id === selectedStage ? "true" : "false"}
              onClick={() => onSelectStage?.(id)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectStage?.(id);
                }
              }}
            >
              <div className="stage-card__header">
                <span>{label}</span>
                <strong>{id === currentStage ? "Active" : "Queued"}</strong>
              </div>
              <p>{description}</p>
              <div className="stage-card__meta">
                <span>{missingCount === 1 ? "1 missing" : `${missingCount} missing`}</span>
                <span>{stageAgents.length} agents</span>
              </div>
              <div className="stage-card__agents">
                {stageAgents.length === 0 ? <em>Human</em> : null}
                {stageAgents.map((agent) => (
                  <span key={agent.id}>
                    {agent.label}
                    <small>{agent.llm_name}</small>
                  </span>
                ))}
              </div>
            </article>
          );
        })}
      </div>

      <div className="agent-roster" aria-label="Agent LLM assignments">
        {agents.map((agent) => (
          <article className="agent-row" key={agent.id} data-active={agent.stages.includes(currentStage)}>
            <h3>{agent.label}</h3>
            <div className="agent-row__model">
              <span>{RUNNER_LABELS[agent.runner] ?? agent.runner}</span>
              <strong>{agent.llm_name}</strong>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
