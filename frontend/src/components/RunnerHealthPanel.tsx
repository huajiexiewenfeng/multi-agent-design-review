import type { RunnerHealth } from "../types/run";

export function RunnerHealthPanel({ runners }: { runners: RunnerHealth[] }) {
  return (
    <section className="runner-health-panel" aria-label="Runner health">
      <div className="section-heading">
        <h2>Runner Health</h2>
        <p>Local CLI availability and command templates.</p>
      </div>
      <div className="runner-health-list">
        {runners.map((runner) => (
          <article className="runner-health-item" data-available={runner.available} key={runner.id}>
            <header>
              <strong>{runner.label}</strong>
              <span>{runner.available ? "available" : "missing"}</span>
            </header>
            <p>{runner.version ?? runner.error ?? "No version detected"}</p>
            <code>{runner.command_template ?? runner.env}</code>
          </article>
        ))}
      </div>
    </section>
  );
}
