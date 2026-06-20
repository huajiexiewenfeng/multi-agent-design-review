import { useState } from "react";
import type { AgentProjection, RunnerSmokeJob, RunnerSmokeResult } from "../types/run";

type AgentConfigUpdate = {
  runner: string;
  model: string;
};

const RUNNER_OPTIONS = [
  ["mock", "Mock"],
  ["manual", "Manual"],
  ["file", "File Drop"],
  ["codex", "Codex"],
  ["claude-code", "Claude Code"],
  ["antigravity", "Antigravity"]
];

const MODEL_OPTIONS: Record<string, string[]> = {
  mock: ["Mock runner"],
  manual: ["Manual CLI"],
  file: ["File drop"],
  codex: ["gpt-5.5"],
  "claude-code": ["opus", "sonnet", "haiku"],
  antigravity: [
    "Gemini 3.5 Flash (High)",
    "Gemini 3.5 Flash (Medium)",
    "Gemini 3.5 Flash (Low)",
    "Gemini 3.1 Pro (High)",
    "Gemini 3.1 Pro (Low)",
    "Claude Opus 4.6 (Thinking)",
    "Claude Sonnet 4.6 (Thinking)",
    "GPT-OSS 120B (Medium)"
  ]
};

function modelFor(agent: AgentProjection): string {
  return agent.model ?? agent.llm_name;
}

function defaultModelForRunner(runner: string): string {
  return MODEL_OPTIONS[runner]?.[0] ?? "";
}

function normalizeModelForRunner(runner: string, model: string): string {
  const options = MODEL_OPTIONS[runner] ?? [];
  if (options.includes(model)) {
    return model;
  }
  return defaultModelForRunner(runner) || model;
}

function isInteractiveOnlyRunner(runner: string): boolean {
  return runner === "antigravity";
}

function smokeDetail(result: RunnerSmokeResult): string {
  if (result.status === "unconfigured") {
    return result.error_message ?? "CLI command is not configured.";
  }
  if (result.status === "waiting_input") {
    return result.error_message ?? "CLI launched but did not write the expected output file.";
  }
  if (result.status === "interactive_only") {
    return result.error_message ?? "Use handoff; this runner opens an interactive workspace.";
  }
  return result.output_content || result.error_message || "";
}

export function AgentSettingsPanel({
  agents,
  onSave,
  smokeResults = {},
  smokeJobs = {},
  testingAgentId = null,
  onSmokeTest
}: {
  agents: AgentProjection[];
  onSave: (agentId: string, update: AgentConfigUpdate) => void;
  smokeResults?: Record<string, RunnerSmokeResult>;
  smokeJobs?: Record<string, RunnerSmokeJob>;
  testingAgentId?: string | null;
  onSmokeTest?: (agentId: string, update: AgentConfigUpdate) => void;
}) {
  const [drafts, setDrafts] = useState<Record<string, AgentConfigUpdate>>(() =>
    Object.fromEntries(
      agents.map((agent) => [
        agent.id,
        { runner: agent.runner, model: normalizeModelForRunner(agent.runner, modelFor(agent)) }
      ])
    )
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
        <p>Choose the local CLI runner and the model passed to that CLI.</p>
      </div>
      <div className="settings-grid">
        {agents.map((agent) => {
          const draft = drafts[agent.id] ?? {
            runner: agent.runner,
            model: normalizeModelForRunner(agent.runner, modelFor(agent))
          };
          const smokeResult = smokeResults[agent.id];
          const smokeJob = smokeJobs[agent.id];
          const availableModels = MODEL_OPTIONS[draft.runner] ?? [];
          const interactiveOnly = isInteractiveOnlyRunner(draft.runner);
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
                  onChange={(event) => {
                    const runner = event.target.value;
                    updateDraft(agent.id, {
                      runner,
                      model: normalizeModelForRunner(runner, draft.model)
                    });
                  }}
                >
                  {RUNNER_OPTIONS.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Model
                <select
                  aria-label={`${agent.label} model`}
                  value={draft.model}
                  onChange={(event) => updateDraft(agent.id, { model: event.target.value })}
                >
                  {availableModels.map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
                {draft.runner === "antigravity" ? (
                  <small className="runner-capability-note">Use handoff; Antigravity opens a trusted workspace.</small>
                ) : null}
              </label>
              <div className="settings-actions">
                <button type="submit">Save</button>
                {onSmokeTest ? (
                  <button
                    className="secondary-action"
                    disabled={interactiveOnly || testingAgentId === agent.id}
                    onClick={() => {
                      if (!interactiveOnly) {
                        onSmokeTest(agent.id, draft);
                      }
                    }}
                    type="button"
                  >
                    {interactiveOnly ? "Interactive only" : testingAgentId === agent.id ? "Testing..." : "Test model"}
                  </button>
                ) : null}
              </div>
              {smokeResult ? (
                <div className="runner-smoke-result agent-smoke-result" data-status={smokeResult.status}>
                  <strong>{smokeResult.status}</strong>
                  <span>{`${smokeResult.runner_id} / ${smokeResult.model ?? draft.model}`}</span>
                  <small>{smokeDetail(smokeResult)}</small>
                </div>
              ) : null}
              {!smokeResult && smokeJob ? (
                <div className="runner-smoke-result agent-smoke-result" data-status={smokeJob.status}>
                  <strong>{smokeJob.status}</strong>
                  <span>{`${smokeJob.runner_id} / ${smokeJob.model ?? draft.model}`}</span>
                  <small>{smokeJob.message}</small>
                </div>
              ) : null}
            </form>
          );
        })}
      </div>
    </section>
  );
}
