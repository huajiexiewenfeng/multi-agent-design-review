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
    <section className="human-input-panel" aria-label="Human input">
      <h3>Human Checkpoint</h3>
      <label>
        Human answers JSON
        <textarea
          aria-label="Human answers JSON"
          value={answersJson}
          onChange={(event) => setAnswersJson(event.target.value)}
          rows={5}
        />
      </label>
      <button type="button" onClick={() => onSaveAnswers(JSON.parse(answersJson))}>
        Save Answers
      </button>
      <label>
        Clarified requirement
        <textarea
          aria-label="Clarified requirement"
          value={clarifiedRequirement}
          onChange={(event) => setClarifiedRequirement(event.target.value)}
          rows={7}
          placeholder="# Clarified Requirement"
        />
      </label>
      <button type="button" onClick={() => onSaveRequirement(clarifiedRequirement)}>
        Save Clarified Requirement
      </button>
    </section>
  );
}
