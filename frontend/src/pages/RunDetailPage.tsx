import { StageBoard } from "../components/StageBoard";
import type { AgentProjection } from "../types/run";

export function RunDetailPage({ stage, agents }: { stage: string; agents?: AgentProjection[] }) {
  return (
    <main>
      <StageBoard currentStage={stage} agents={agents} />
      <section aria-label="Current stage content" />
    </main>
  );
}
