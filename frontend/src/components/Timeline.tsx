export type TimelineEvent = {
  id: string;
  actor: string;
  event_type: string;
  message: string;
};

export function Timeline({ events }: { events: TimelineEvent[] }) {
  return (
    <aside aria-label="Timeline">
      {events.map((event) => (
        <article key={event.id}>
          <strong>{event.actor}</strong>
          <span>{event.event_type}</span>
          <p>{event.message}</p>
        </article>
      ))}
    </aside>
  );
}
