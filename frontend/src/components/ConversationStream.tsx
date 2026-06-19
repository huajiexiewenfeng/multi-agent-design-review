import type { ConversationMessage } from "../viewModels/workbenchViewModel";

export function ConversationStream({ messages }: { messages: ConversationMessage[] }) {
  return (
    <section className="conversation-stream" aria-label="Agent conversation">
      <div className="conversation-stream__messages">
        {messages.length === 0 ? <p className="empty-state">No conversation yet.</p> : null}
        {messages.map((message) => (
          <article className="conversation-message" key={message.id} data-actor-type={message.actorType}>
            <div className="conversation-message__avatar" aria-hidden="true">
              {message.actorLabel.charAt(0).toUpperCase()}
            </div>
            <div className="conversation-message__content">
              <header>
                <strong>{message.actorLabel}</strong>
                <span>{message.actorType}</span>
                {message.runnerLabel && message.llmName ? <span>{`${message.runnerLabel} / ${message.llmName}`}</span> : null}
                {message.stage ? <span>{message.stage}</span> : null}
              </header>
              <div className="conversation-message__body">
                {message.body.split("\n").map((line, index) => (
                  <p key={`${message.id}_${index}`}>{line}</p>
                ))}
              </div>
              {message.relatedFile ? <footer>{message.relatedFile}</footer> : null}
            </div>
          </article>
        ))}
      </div>

      <form className="conversation-composer">
        <textarea aria-label="Conversation composer" placeholder="Ask a question or provide additional context..." />
        <button type="submit" disabled>
          Send
        </button>
      </form>
    </section>
  );
}
