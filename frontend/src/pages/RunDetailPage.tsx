import { StageBoard } from "../components/StageBoard";

export function RunDetailPage({ stage }: { stage: string }) {
  return (
    <main>
      <StageBoard currentStage={stage} />
      <section aria-label="Current stage content" />
    </main>
  );
}
