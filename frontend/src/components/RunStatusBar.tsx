import type { WorkbenchJobStatus } from "../viewModels/workbenchViewModel";

export function RunStatusBar({
  currentStageLabel,
  humanActionCount,
  statusMessage,
  jobStatus
}: {
  currentStageLabel: string;
  humanActionCount: number;
  statusMessage: string;
  jobStatus: WorkbenchJobStatus | null;
}) {
  const waitingForHuman = !jobStatus && humanActionCount > 0;
  const stateLabel = waitingForHuman ? "Waiting for human" : jobStatus ? statusLabel(jobStatus.status) : "Ready";
  const detail = jobStatus?.message ?? statusMessage;

  return (
    <section className="run-status-bar" aria-label="Run status" data-state={jobStatus?.status ?? "idle"}>
      <div>
        <span>Current stage</span>
        <strong>{currentStageLabel}</strong>
      </div>
      <div>
        <span>State</span>
        <strong>{stateLabel}</strong>
      </div>
      {humanActionCount > 0 ? (
        <div>
          <span>Human actions</span>
          <strong>
            {humanActionCount} {humanActionCount === 1 ? "action required" : "actions required"}
          </strong>
        </div>
      ) : null}
      {detail ? <p>{detail}</p> : null}
    </section>
  );
}

function statusLabel(status: WorkbenchJobStatus["status"]): string {
  const labels: Record<WorkbenchJobStatus["status"], string> = {
    queued: "Queued",
    running: "Running",
    succeeded: "Succeeded",
    failed: "Failed"
  };
  return labels[status];
}
