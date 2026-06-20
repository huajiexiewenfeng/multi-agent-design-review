import { useState } from "react";

export function HumanInputPanel({
  onSaveAnswers,
  onSaveRequirement
}: {
  onSaveAnswers: (content: string) => void;
  onSaveRequirement: (content: string) => void;
}) {
  const [answersText, setAnswersText] = useState("");
  const [clarifiedRequirement, setClarifiedRequirement] = useState("");
  return (
    <section className="human-input-panel" aria-label="Human input">
      <h3>Human Checkpoint</h3>
      <label>
        Human answers
        <textarea
          aria-label="Human answers"
          value={answersText}
          onChange={(event) => setAnswersText(event.target.value)}
          rows={5}
          placeholder="Write your answers, decisions, or extra context in natural language."
        />
      </label>
      <button
        type="button"
        disabled={!answersText.trim()}
        onClick={() => onSaveAnswers(answersText.trim())}
      >
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
