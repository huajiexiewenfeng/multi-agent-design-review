import { useState } from "react";

export function SubmitOutputDialog({
  agentId,
  stage,
  onSubmit
}: {
  agentId: string;
  stage: string;
  onSubmit: (agentId: string, stage: string, content: string) => void;
}) {
  const [content, setContent] = useState("");
  return (
    <section>
      <h2>Submit {agentId}</h2>
      <label>
        Agent output
        <textarea value={content} onChange={(event) => setContent(event.target.value)} />
      </label>
      <button onClick={() => onSubmit(agentId, stage, content)}>Submit</button>
    </section>
  );
}
