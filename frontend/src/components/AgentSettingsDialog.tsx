import { useState } from "react";
import { createPortal } from "react-dom";
import { AgentSettingsPanel } from "./AgentSettingsPanel";
import type { AgentProjection, RunnerSmokeJob, RunnerSmokeResult } from "../types/run";

type AgentConfigUpdate = {
  runner: string;
  model: string;
};

export function AgentSettingsDialog({
  agents,
  onSave,
  smokeResults,
  smokeJobs,
  testingAgentId,
  onSmokeTest
}: {
  agents: AgentProjection[];
  onSave: (agentId: string, update: AgentConfigUpdate) => void;
  smokeResults?: Record<string, RunnerSmokeResult>;
  smokeJobs?: Record<string, RunnerSmokeJob>;
  testingAgentId?: string | null;
  onSmokeTest?: (agentId: string, update: AgentConfigUpdate) => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="agent-settings-dialog">
      <button type="button" className="secondary-action" disabled={agents.length === 0} onClick={() => setOpen(true)}>
        Agent settings
      </button>

      {open
        ? createPortal(
            <div className="dialog-backdrop" role="presentation">
              <section className="settings-dialog" role="dialog" aria-modal="true" aria-label="Agent settings">
                <header>
                  <div>
                    <h2>Agent settings</h2>
                    <p>Configure each role's local CLI runner and model.</p>
                  </div>
                  <button type="button" aria-label="Close agent settings" onClick={() => setOpen(false)}>
                    Close
                  </button>
                </header>
                <AgentSettingsPanel
                  agents={agents}
                  onSave={onSave}
                  smokeResults={smokeResults}
                  smokeJobs={smokeJobs}
                  testingAgentId={testingAgentId}
                  onSmokeTest={onSmokeTest}
                />
              </section>
            </div>,
            document.body
          )
        : null}
    </div>
  );
}
