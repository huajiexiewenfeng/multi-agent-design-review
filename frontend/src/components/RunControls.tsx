export function RunControls({
  disabled,
  canFinalize = false,
  isRunning = false,
  onRunStep,
  onFinalize
}: {
  disabled: boolean;
  canFinalize?: boolean;
  isRunning?: boolean;
  onRunStep: () => void;
  onFinalize: () => void;
}) {
  return (
    <section className="run-controls" aria-label="Run controls">
      <div>
        <h2>Flow Control</h2>
        <p>Generate prompts and advance one LangGraph step for the selected run.</p>
      </div>
      <div className="run-control-actions">
        <button type="button" disabled={disabled || isRunning} onClick={onRunStep}>
          {isRunning ? "Running..." : "Run Graph Step"}
        </button>
        <button type="button" disabled={disabled || isRunning || !canFinalize} onClick={onFinalize}>
          Finalize Output
        </button>
      </div>
    </section>
  );
}
