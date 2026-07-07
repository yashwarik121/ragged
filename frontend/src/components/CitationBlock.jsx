export default function CitationBlock({ claim, source, passage }) {
  return (
    <article className="citation-block" id={`citation-${source}`}>
      <p className="citation-block__claim">{claim}</p>
      <span className="citation-block__source">
        {source}
        {passage && (
          <span className="citation-block__tooltip">{passage}</span>
        )}
      </span>
    </article>
  );
}
