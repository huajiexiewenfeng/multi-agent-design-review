import type { RunnerHealth, RunnerSmokeResult } from "../types/run";

type RunnerHealthPanelProps = {
  runners: RunnerHealth[];
  smokeResults?: Record<string, RunnerSmokeResult>;
  testingRunnerId?: string | null;
  onSmokeTest?: (runnerId: string) => void;
};

export function RunnerHealthPanel({
  runners,
  smokeResults = {},
  testingRunnerId = null,
  onSmokeTest
}: RunnerHealthPanelProps) {
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
            {onSmokeTest ? (
              <button
                className="secondary-action"
                disabled={!runner.configured || testingRunnerId === runner.id}
                onClick={() => onSmokeTest(runner.id)}
                type="button"
              >
                {testingRunnerId === runner.id ? "Testing..." : `Test ${runner.label}`}
              </button>
            ) : null}
            {smokeResults[runner.id] ? (
              <div className="runner-smoke-result" data-status={smokeResults[runner.id].status}>
                <strong>{smokeResults[runner.id].status}</strong>
                <span>{smokeResults[runner.id].output_content || smokeResults[runner.id].error_message}</span>
              </div>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
