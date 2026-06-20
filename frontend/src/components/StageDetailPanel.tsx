import { useEffect, useMemo, useState } from "react";
import { HumanInputPanel } from "./HumanInputPanel";
import type { AgentProjection, StageArtifact } from "../types/run";

export function StageDetailPanel({
  stage,
  artifacts,
  missingInputs,
  agents = [],
  onSubmitOutput,
  onSaveAnswers,
  onSaveRequirement,
  onSkipAgent
}: {
  stage: string;
  artifacts: StageArtifact[];
  missingInputs: string[];
  agents?: AgentProjection[];
  onSubmitOutput?: (agentId: string, stage: string, content: string) => void;
  onSaveAnswers?: (content: string) => void;
  onSaveRequirement?: (content: string) => void;
  onSkipAgent?: (agentId: string, stage: string, reason: string) => void;
}) {
  const stageAgents = useMemo(() => {
    const participatingAgents = agents.filter((agent) => agent.stages.includes(stage));
    return participatingAgents.length > 0 ? participatingAgents : agents;
  }, [agents, stage]);
  const [agentId, setAgentId] = useState(stageAgents[0]?.id ?? "");
  const [content, setContent] = useState("");
  const [skipAgentId, setSkipAgentId] = useState(stageAgents[0]?.id ?? "");
  const [skipReason, setSkipReason] = useState("");
  const prompts = artifacts.filter((artifact) => artifact.kind === "prompt");
  const outputs = artifacts.filter((artifact) => artifact.kind === "output");
  const canSubmit = Boolean(onSubmitOutput && agentId && content.trim());
  const canSkip = Boolean(onSkipAgent && skipAgentId && skipReason.trim());

  useEffect(() => {
    setAgentId(stageAgents[0]?.id ?? "");
    setSkipAgentId(stageAgents[0]?.id ?? "");
    setContent("");
    setSkipReason("");
  }, [stage, stageAgents]);

  function submitOutput() {
    if (!canSubmit || !onSubmitOutput) {
      return;
    }
    onSubmitOutput(agentId, stage, content);
    setContent("");
  }

  function skipAgent() {
    if (!canSkip || !onSkipAgent) {
      return;
    }
    onSkipAgent(skipAgentId, stage, skipReason);
    setSkipReason("");
  }

  return (
    <section className="stage-detail" aria-label="Stage detail">
      <div className="section-heading">
        <h2>Stage Detail</h2>
        <p>{stage}</p>
      </div>

      {onSubmitOutput ? (
        <div className="stage-submit-form">
          <h3>Submit Agent Output</h3>
          <label>
            Output agent
            <select aria-label="Output agent" value={agentId} onChange={(event) => setAgentId(event.target.value)}>
              {stageAgents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.label} - {agent.llm_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Agent output markdown
            <textarea
              aria-label="Agent output markdown"
              value={content}
              onChange={(event) => setContent(event.target.value)}
              rows={8}
              placeholder="Paste or edit the agent response here."
            />
          </label>
          <button type="button" disabled={!canSubmit} onClick={submitOutput}>
            Submit Output
          </button>
        </div>
      ) : null}

      {stage === "clarified_requirement" && onSaveAnswers && onSaveRequirement ? (
        <HumanInputPanel onSaveAnswers={onSaveAnswers} onSaveRequirement={onSaveRequirement} />
      ) : null}

      {onSkipAgent && stageAgents.length > 0 ? (
        <div className="stage-submit-form">
          <h3>Skip Blocking Agent</h3>
          <label>
            Skip agent
            <select aria-label="Skip agent" value={skipAgentId} onChange={(event) => setSkipAgentId(event.target.value)}>
              {stageAgents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.label} - {agent.llm_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Skip reason
            <textarea
              aria-label="Skip reason"
              value={skipReason}
              onChange={(event) => setSkipReason(event.target.value)}
              rows={3}
              placeholder="Explain why this agent should not block the current stage."
            />
          </label>
          <button type="button" disabled={!canSkip} onClick={skipAgent}>
            Skip Agent
          </button>
        </div>
      ) : null}

      <ArtifactGroup title="Prompts" artifacts={prompts} emptyText="No prompts generated yet." />
      <ArtifactGroup title="Outputs" artifacts={outputs} emptyText="No agent outputs imported yet." />

      <div className="artifact-group">
        <h3>Missing Inputs</h3>
        {missingInputs.length === 0 ? <p className="empty-state">Nothing missing for this stage.</p> : null}
        {missingInputs.map((item) => (
          <code className="missing-item" key={item}>
            {item}
          </code>
        ))}
      </div>
    </section>
  );
}

function ArtifactGroup({
  title,
  artifacts,
  emptyText
}: {
  title: string;
  artifacts: StageArtifact[];
  emptyText: string;
}) {
  return (
    <div className="artifact-group">
      <h3>{title}</h3>
      {artifacts.length === 0 ? <p className="empty-state">{emptyText}</p> : null}
      {artifacts.map((artifact) => (
        <article className="artifact-item" key={`${artifact.kind}:${artifact.path}`}>
          <header>
            <strong>{artifact.agent_id ?? "human"}</strong>
            <span>{artifact.kind}</span>
          </header>
          <code>{artifact.path}</code>
          <pre>{artifact.content}</pre>
        </article>
      ))}
    </div>
  );
}
