export default function Flashcard({ terms = [] }) {
  if (!terms.length) return null;

  return (
    <section id="flashcards">
      <div className="flashcards__label">
        {String(terms.length).padStart(2, '0')} TERMS EXTRACTED
      </div>
      <div className="flashcards__list">
        {terms.map((item, i) => (
          <div className="flashcard-row stagger-in" key={i} id={`flashcard-${i}`}>
            <span className="flashcard-row__term">{item.term}</span>
            <span className="flashcard-row__sep">:</span>
            <span className="flashcard-row__def">{item.definition}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
