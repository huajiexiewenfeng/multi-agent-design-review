import type { FlowVerification } from "../types/run";

export function FlowVerificationPanel({ verification }: { verification: FlowVerification | null }) {
  return (
    <section className="flow-verification-panel" aria-label="Flow verification">
      <div className="section-heading">
        <h2>Flow Verification</h2>
        <p>Evidence that final docs and local runners participated in this run.</p>
      </div>
      {!verification ? <p className="empty-state">No verification loaded.</p> : null}
      {verification ? (
        <>
          <strong className="verification-status" data-complete={verification.complete ? "true" : "false"}>
            {verification.complete ? "Complete" : "Incomplete"}
          </strong>
          <div className="verification-output-list">
            {verification.final_outputs.map((output) => (
              <article className="verification-output-item" data-ready={output.ready ? "true" : "false"} key={output.path}>
                <strong>{output.path}</strong>
                <span>{output.ready ? "ready" : output.exists ? "empty" : "missing"}</span>
              </article>
            ))}
          </div>
          <div className="verification-runner-list">
            {verification.runners.map((runner) => (
              <article className="verification-runner-item" data-satisfied={runner.satisfied ? "true" : "false"} key={runner.runner}>
                <header>
                  <strong>{runner.runner}</strong>
                  <span>{runner.satisfied ? "satisfied" : "missing"}</span>
                </header>
                {runner.evidence.length === 0 ? <p>No runner evidence yet.</p> : null}
                {runner.evidence.map((event) => (
                  <p key={event.event_id}>
                    <code>{event.event_type}</code> {event.agent_id} / {event.stage}
                  </p>
                ))}
              </article>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}
