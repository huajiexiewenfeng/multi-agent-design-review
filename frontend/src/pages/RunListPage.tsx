import { StageBoard } from "../components/StageBoard";

export function RunListPage() {
  return (
    <main>
      <h1>Multi-Agent Design Review</h1>
      <StageBoard currentStage="requirement" />
    </main>
  );
}
