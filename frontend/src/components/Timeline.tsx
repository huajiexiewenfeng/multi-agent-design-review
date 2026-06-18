import type { TimelineEvent } from "../types/run";

export function Timeline({ events }: { events: TimelineEvent[] }) {
  return (
    <aside className="discussion-panel" aria-label="Discussion timeline">
      <div className="section-heading">
        <h2>Discussion</h2>
        <p>Human, system, and agent messages in one timeline.</p>
      </div>
      <div className="timeline-list">
        {events.length === 0 ? <p className="empty-state">No events yet.</p> : null}
        {events.map((event) => (
          <article className="timeline-item" key={event.id} data-actor-type={event.actor_type ?? "agent"}>
            <div className="timeline-item__meta">
              <strong>{event.actor}</strong>
              <span>{event.event_type}</span>
            </div>
            <p>{event.message}</p>
            <footer>
              {event.stage ? <span>{event.stage}</span> : null}
              {event.related_file ? <span>{event.related_file}</span> : null}
            </footer>
          </article>
        ))}
      </div>
    </aside>
  );
}
