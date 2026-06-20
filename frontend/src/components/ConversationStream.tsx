import type { ConversationMessage } from "../viewModels/workbenchViewModel";

type ConversationStreamProps = {
  messages: ConversationMessage[];
  filePreviews?: Record<string, string>;
  onOpenRelatedFile?: (path: string) => void;
};

function renderLines(id: string, content: string) {
  return content.split("\n").map((line, index) => <p key={`${id}_${index}`}>{line}</p>);
}

export function ConversationStream({ messages, filePreviews = {}, onOpenRelatedFile }: ConversationStreamProps) {
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
                {renderLines(message.id, message.body)}
              </div>
              {message.relatedFile ? (
                <footer className="conversation-message__attachment">
                  <button type="button" onClick={() => onOpenRelatedFile?.(message.relatedFile as string)}>
                    Open <span>{message.relatedFile}</span>
                  </button>
                  {filePreviews[message.relatedFile] ? (
                    <div className="conversation-message__preview" aria-label={`${message.relatedFile} preview`}>
                      {renderLines(`${message.id}_preview`, filePreviews[message.relatedFile])}
                    </div>
                  ) : null}
                </footer>
              ) : null}
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
