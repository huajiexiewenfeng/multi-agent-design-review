import { useState } from "react";

export function HumanInputPanel({
  onSaveAnswers,
  onSaveRequirement
}: {
  onSaveAnswers: (answers: Record<string, string>) => void;
  onSaveRequirement: (content: string) => void;
}) {
  const [answersJson, setAnswersJson] = useState("{}");
  const [clarifiedRequirement, setClarifiedRequirement] = useState("");
  return (
    <section aria-label="Human input">
      <h2>Human Input</h2>
      <label>
        Human answers JSON
        <textarea value={answersJson} onChange={(event) => setAnswersJson(event.target.value)} />
      </label>
      <button onClick={() => onSaveAnswers(JSON.parse(answersJson))}>Save Answers</button>
      <label>
        Clarified requirement
        <textarea value={clarifiedRequirement} onChange={(event) => setClarifiedRequirement(event.target.value)} />
      </label>
      <button onClick={() => onSaveRequirement(clarifiedRequirement)}>Save Clarified Requirement</button>
    </section>
  );
}
