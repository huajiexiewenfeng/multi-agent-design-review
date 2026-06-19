import type { StageRailItem } from "../viewModels/workbenchViewModel";

export function StageProgressRail({
  stages,
  selectedStage,
  onSelectStage
}: {
  stages: StageRailItem[];
  selectedStage?: string;
  onSelectStage?: (stageId: string) => void;
}) {
  return (
    <nav className="stage-progress-rail" aria-label="Stage progress">
      {stages.map((stage, index) => (
        <button
          className="stage-progress-item"
          key={stage.id}
          type="button"
          aria-label={`${stage.label} stage`}
          data-state={stage.state}
          data-selected={stage.id === selectedStage ? "true" : "false"}
          onClick={() => onSelectStage?.(stage.id)}
        >
          <span className="stage-progress-item__marker" aria-hidden="true">
            {stage.state === "complete" ? "✓" : index + 1}
          </span>
          <span className="stage-progress-item__body">
            <strong>{stage.label}</strong>
            <small>{stateLabel(stage.state)}</small>
            {stage.missingCount > 0 ? (
              <em>
                {stage.missingCount} {stage.missingCount === 1 ? "missing input" : "missing inputs"}
              </em>
            ) : null}
          </span>
        </button>
      ))}
    </nav>
  );
}

function stateLabel(state: StageRailItem["state"]): string {
  const labels: Record<StageRailItem["state"], string> = {
    complete: "Complete",
    in_progress: "In progress",
    blocked: "Blocked",
    pending: "Pending",
    failed: "Failed"
  };
  return labels[state];
}
