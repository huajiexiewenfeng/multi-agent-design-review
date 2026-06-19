import { useState } from "react";
import { createPortal } from "react-dom";
import { AgentSettingsPanel } from "./AgentSettingsPanel";
import type { AgentProjection } from "../types/run";

type AgentConfigUpdate = {
  runner: string;
  llm_name: string;
};

export function AgentSettingsDialog({
  agents,
  onSave
}: {
  agents: AgentProjection[];
  onSave: (agentId: string, update: AgentConfigUpdate) => void;
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
                    <p>Configure each role's local runner and visible LLM name.</p>
                  </div>
                  <button type="button" aria-label="Close agent settings" onClick={() => setOpen(false)}>
                    Close
                  </button>
                </header>
                <AgentSettingsPanel agents={agents} onSave={onSave} />
              </section>
            </div>,
            document.body
          )
        : null}
    </div>
  );
}
