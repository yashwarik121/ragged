export default function Timeline({ events = [] }) {
  if (!events.length) return null;

  return (
    <section className="timeline" id="timeline">
      <div className="timeline__label">TIMELINE</div>
      {events.map((event, i) => (
        <div className="timeline__entry stagger-in" key={i} id={`timeline-entry-${i}`}>
          <div className="timeline__date">{event.date}</div>
          <div className="timeline__text">{event.text}</div>
        </div>
      ))}
    </section>
  );
}
