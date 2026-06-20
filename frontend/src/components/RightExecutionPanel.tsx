import { useState } from "react";
import type {
  AgentQueueItem,
  FinalOutputItem,
  HumanActionItem,
  WorkbenchArtifact
} from "../viewModels/workbenchViewModel";

export function RightExecutionPanel({
  agentQueue,
  humanActions,
  artifacts,
  finalOutputs,
  finalOutputPreviews = {},
  canFinalize,
  isImportingHandoffs,
  onFinalize,
  onImportHandoffs,
  onSubmitHumanInput,
  onOpenFinalOutput,
  onCopyFinalOutput,
  onDownloadFinalOutput,
  onRequestChanges
}: {
  agentQueue: AgentQueueItem[];
  humanActions: HumanActionItem[];
  artifacts: WorkbenchArtifact[];
  finalOutputs: FinalOutputItem[];
  finalOutputPreviews?: Record<string, string>;
  canFinalize: boolean;
  isImportingHandoffs: boolean;
  onFinalize: () => void;
  onImportHandoffs: () => void;
  onSubmitHumanInput?: (action: HumanActionItem, content: string) => void;
  onOpenFinalOutput?: (output: FinalOutputItem) => void;
  onCopyFinalOutput?: (output: FinalOutputItem) => void;
  onDownloadFinalOutput?: (output: FinalOutputItem) => void;
  onRequestChanges?: (content: string) => void;
}) {
  const [humanResponses, setHumanResponses] = useState<Record<string, string>>({});
  const [changeRequest, setChangeRequest] = useState("");

  function submitHumanInput(action: HumanActionItem) {
    const content = humanResponses[action.id]?.trim() ?? "";
    if (!content || !onSubmitHumanInput) {
      return;
    }
    onSubmitHumanInput(action, content);
    setHumanResponses((current) => ({ ...current, [action.id]: "" }));
  }

  function submitChangeRequest() {
    const content = changeRequest.trim();
    if (!content || !onRequestChanges) {
      return;
    }
    onRequestChanges(content);
    setChangeRequest("");
  }

  return (
    <aside className="right-execution-panel" aria-label="Execution panel">
      <section className="execution-section">
        <div className="execution-section__header">
          <h2>Agent Queue</h2>
          <span>{agentQueue.length}</span>
        </div>
        {agentQueue.length === 0 ? <p className="empty-state">No agents configured.</p> : null}
        {agentQueue.map((agent) => (
          <article className="agent-queue-row" key={agent.id} data-status={agent.status}>
            <div>
              <strong>{agent.label}</strong>
              <span>{`${agent.runnerLabel} / ${agent.llmName}`}</span>
              <small>{agent.task}</small>
            </div>
            <em>{statusLabel(agent.status)}</em>
          </article>
        ))}
      </section>

      <section className="execution-section">
        <div className="execution-section__header">
          <h2>Human Action Required</h2>
          <span>{humanActions.length}</span>
        </div>
        {humanActions.length === 0 ? <p className="empty-state">No human action required.</p> : null}
        {humanActions.map((action) => (
          <article className="human-action-card" key={action.id}>
            <strong>{action.title}</strong>
            <p>{action.description}</p>
            <small>{action.inputLabel}</small>
            {onSubmitHumanInput ? (
              <label>
                Human response
                <textarea
                  aria-label="Human response"
                  value={humanResponses[action.id] ?? ""}
                  onChange={(event) =>
                    setHumanResponses((current) => ({
                      ...current,
                      [action.id]: event.target.value
                    }))
                  }
                  rows={4}
                  placeholder="Write your answer, decision, or confirmation in natural language."
                />
              </label>
            ) : null}
            {onSubmitHumanInput ? (
              <button
                type="button"
                disabled={!(humanResponses[action.id] ?? "").trim()}
                onClick={() => submitHumanInput(action)}
              >
                Save response
              </button>
            ) : null}
          </article>
        ))}
      </section>

      <section className="execution-section">
        <div className="execution-section__header">
          <h2>Artifacts</h2>
          <span>{artifacts.length}</span>
        </div>
        {artifacts.length === 0 ? <p className="empty-state">No artifacts for this view.</p> : null}
        {artifacts.map((artifact) => (
          <article className="artifact-row" key={artifact.path}>
            <strong>{artifact.path}</strong>
            <span>{artifact.kind}</span>
            {artifact.agentId ? <small>{artifact.agentId}</small> : null}
          </article>
        ))}
      </section>

      <section className="execution-section">
        <div className="execution-section__header">
          <h2>Final Outputs</h2>
          <button type="button" disabled={!canFinalize} onClick={onFinalize}>
            Generate final docs
          </button>
        </div>
        {finalOutputs.map((output) => (
          <article className="final-output-row" key={output.path} data-ready={output.ready ? "true" : "false"}>
            <div>
              <strong>{output.label}</strong>
              <span>{output.path}</span>
            </div>
            <em>{output.ready ? "Ready" : output.exists ? "Incomplete" : "Missing"}</em>
            {onOpenFinalOutput ? (
              <button type="button" disabled={!output.exists} onClick={() => onOpenFinalOutput(output)}>
                Open {output.label}
              </button>
            ) : null}
            {onCopyFinalOutput || onDownloadFinalOutput ? (
              <div className="final-output-actions">
                {onCopyFinalOutput ? (
                  <button type="button" disabled={!output.exists} onClick={() => onCopyFinalOutput(output)}>
                    Copy {output.label} path
                  </button>
                ) : null}
                {onDownloadFinalOutput ? (
                  <button type="button" disabled={!output.exists} onClick={() => onDownloadFinalOutput(output)}>
                    Download {output.label}
                  </button>
                ) : null}
              </div>
            ) : null}
            {finalOutputPreviews[output.path] ? (
              <div className="final-output-preview" aria-label={`${output.label} preview`}>
                {finalOutputPreviews[output.path].split("\n").map((line, index) => (
                  <p key={`${output.path}_${index}`}>{line}</p>
                ))}
              </div>
            ) : null}
          </article>
        ))}
        {onRequestChanges ? (
          <div className="final-change-request">
            <label>
              Request changes
              <textarea
                aria-label="Request changes"
                value={changeRequest}
                onChange={(event) => setChangeRequest(event.target.value)}
                rows={3}
                placeholder="Ask the agents to continue the discussion before finalizing."
              />
            </label>
            <button type="button" disabled={!changeRequest.trim()} onClick={submitChangeRequest}>
              Request changes
            </button>
          </div>
        ) : null}
      </section>

      <section className="execution-section">
        <div className="execution-section__header">
          <h2>Debug</h2>
          <button type="button" disabled={isImportingHandoffs} onClick={onImportHandoffs}>
            {isImportingHandoffs ? "Checking..." : "Check runner outputs"}
          </button>
        </div>
        <p>Runner logs, handoffs, health, and verification stay here for troubleshooting.</p>
      </section>
    </aside>
  );
}

function statusLabel(status: AgentQueueItem["status"]): string {
  const labels: Record<AgentQueueItem["status"], string> = {
    complete: "Complete",
    in_progress: "In progress",
    blocked: "Blocked",
    pending: "Pending",
    failed: "Failed",
    waiting_input: "Waiting input"
  };
  return labels[status];
}
