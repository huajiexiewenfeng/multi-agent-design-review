export function RunControls({
  disabled,
  canFinalize = false,
  onRunStep,
  onFinalize
}: {
  disabled: boolean;
  canFinalize?: boolean;
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
        <button type="button" disabled={disabled} onClick={onRunStep}>
          Run Graph Step
        </button>
        <button type="button" disabled={disabled || !canFinalize} onClick={onFinalize}>
          Finalize Output
        </button>
      </div>
    </section>
  );
}
