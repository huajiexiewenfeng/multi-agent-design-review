import { useState } from "react";
import type { AgentProjection } from "../types/run";

type AgentConfigUpdate = {
  runner: string;
  llm_name: string;
};

const RUNNER_OPTIONS = [
  ["mock", "Mock"],
  ["manual", "Manual"],
  ["file", "File Drop"],
  ["codex", "Codex"],
  ["claude-code", "Claude Code"],
  ["antigravity", "Antigravity"]
];

export function AgentSettingsPanel({
  agents,
  onSave
}: {
  agents: AgentProjection[];
  onSave: (agentId: string, update: AgentConfigUpdate) => void;
}) {
  const [drafts, setDrafts] = useState<Record<string, AgentConfigUpdate>>(() =>
    Object.fromEntries(agents.map((agent) => [agent.id, { runner: agent.runner, llm_name: agent.llm_name }]))
  );

  function updateDraft(agentId: string, patch: Partial<AgentConfigUpdate>) {
    setDrafts((current) => ({
      ...current,
      [agentId]: {
        ...current[agentId],
        ...patch
      }
    }));
  }

  return (
    <section className="settings-panel" aria-label="Agent settings">
      <div className="section-heading">
        <h2>Agent Models</h2>
        <p>Choose the local runner and visible LLM name for each role.</p>
      </div>
      <div className="settings-grid">
        {agents.map((agent) => {
          const draft = drafts[agent.id] ?? { runner: agent.runner, llm_name: agent.llm_name };
          return (
            <form
              className="settings-row"
              key={agent.id}
              onSubmit={(event) => {
                event.preventDefault();
                onSave(agent.id, draft);
              }}
            >
              <h3>{agent.label}</h3>
              <label>
                Runner
                <select
                  aria-label={`${agent.label} runner`}
                  value={draft.runner}
                  onChange={(event) => updateDraft(agent.id, { runner: event.target.value })}
                >
                  {RUNNER_OPTIONS.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                LLM name
                <input
                  aria-label={`${agent.label} LLM name`}
                  value={draft.llm_name}
                  onChange={(event) => updateDraft(agent.id, { llm_name: event.target.value })}
                  placeholder="claude-sonnet-4.5"
                />
              </label>
              <button type="submit">Save {agent.label}</button>
            </form>
          );
        })}
      </div>
    </section>
  );
}
