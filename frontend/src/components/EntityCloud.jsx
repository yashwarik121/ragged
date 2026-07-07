const GROUPS = [
  { key: 'people', label: 'PEOPLE' },
  { key: 'organizations', label: 'ORGANIZATIONS' },
  { key: 'places', label: 'PLACES' },
  { key: 'dates', label: 'DATES' },
];

export default function EntityCloud({ entities = {} }) {
  const hasAny = GROUPS.some(g => entities[g.key]?.length > 0);
  if (!hasAny) return null;

  return (
    <section className="entity-cloud" id="entity-cloud">
      {GROUPS.map(group => {
        const items = entities[group.key];
        if (!items || items.length === 0) return null;

        return (
          <div className="entity-cloud__group" key={group.key} id={`entity-group-${group.key}`}>
            <div className="entity-cloud__label">{group.label}</div>
            <div className="entity-cloud__tags">
              {items.map((name, i) => (
                <span className="entity-tag" key={i}>{name}</span>
              ))}
            </div>
          </div>
        );
      })}
    </section>
  );
}
