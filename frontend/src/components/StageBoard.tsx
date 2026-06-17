const STAGES = [
  ["requirement", "Requirement"],
  ["clarification", "Clarification"],
  ["clarified_requirement", "Clarified Requirement"],
  ["draft_design", "Draft Design"],
  ["cross_review", "Cross Review"],
  ["revision", "Revision"],
  ["synthesis", "Synthesis"]
];

export function StageBoard({ currentStage }: { currentStage: string }) {
  return (
    <nav aria-label="Workflow stages">
      {STAGES.map(([id, label]) => (
        <button key={id} data-current={id === currentStage ? "true" : "false"}>
          {label}
        </button>
      ))}
    </nav>
  );
}
