import type { RunnerLog } from "../types/run";

export function RunnerLogsPanel({ logs }: { logs: RunnerLog[] }) {
  return (
    <section className="runner-logs-panel" aria-label="Runner logs">
      <div className="section-heading">
        <h2>Runner Logs</h2>
        <p>Command output and failures from local agents.</p>
      </div>
      {logs.length === 0 ? <p className="empty-state">No runner logs yet.</p> : null}
      <div className="runner-log-list">
        {logs.map((log) => (
          <article className="runner-log-item" key={log.path}>
            <header>
              <strong>{log.agent_id}</strong>
              <span>{log.path}</span>
            </header>
            <pre>{log.content}</pre>
          </article>
        ))}
      </div>
    </section>
  );
}
