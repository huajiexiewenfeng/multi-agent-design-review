import type { RunnerHandoff } from "../types/run";

export function RunnerHandoffsPanel({
  handoffs,
  onImport,
  isImporting = false
}: {
  handoffs: RunnerHandoff[];
  onImport?: () => void;
  isImporting?: boolean;
}) {
  return (
    <section className="runner-handoffs-panel" aria-label="Runner handoffs">
      <div className="section-heading">
        <h2>Runner Handoffs</h2>
        <p>Agents waiting for an external CLI session to write output.</p>
      </div>
      {handoffs.length === 0 ? <p className="empty-state">No runner handoffs waiting.</p> : null}
      {handoffs.length > 0 && onImport ? (
        <button className="secondary-action" disabled={isImporting} onClick={onImport} type="button">
          {isImporting ? "Checking..." : "Check Outputs"}
        </button>
      ) : null}
      <div className="runner-handoff-list">
        {handoffs.map((handoff) => (
          <article className="runner-handoff-item" key={handoff.event_id}>
            <header>
              <strong>{handoff.agent_id}</strong>
              <span>{handoff.stage}</span>
            </header>
            <p>{handoff.message}</p>
            {handoff.output_file ? <code>{handoff.output_file}</code> : null}
            {handoff.instruction_file ? <span className="handoff-path">{handoff.instruction_file}</span> : null}
            {handoff.instruction ? <pre>{handoff.instruction}</pre> : null}
          </article>
        ))}
      </div>
    </section>
  );
}
