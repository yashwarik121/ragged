import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import TextScramble from '../components/TextScramble';
import Flashcard from '../components/Flashcard';
import EntityCloud from '../components/EntityCloud';
import Timeline from '../components/Timeline';

const API = 'http://localhost:8000';

export default function CheatSheet({ setDocInfo }) {
  const { docId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await axios.get(`${API}/cheatsheet/${docId}`);
        setData(res.data);
        setDocInfo({ id: docId, name: res.data.document_name || res.data.title || docId });
        setError(null);
      } catch (err) {
        console.error('Failed to fetch cheatsheet:', err);
        setError('FAILED TO LOAD CHEAT SHEET');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [docId]);

  if (loading) {
    return (
      <main className="page" id="page-cheatsheet">
        <div className="loading-bar"><div className="loading-bar__inner" /></div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page" id="page-cheatsheet">
        <div className="state-message state-message--error">{error}</div>
      </main>
    );
  }

  const terms = data?.flashcards || [];
  const insights = data?.key_insights || [];
  const entities = data?.entities || {};
  // Backend returns timeline as a list of date strings — convert to {date, text} objects
  const rawTimeline = data?.timeline || [];
  const timeline = rawTimeline.map(item =>
    typeof item === 'string' ? { date: item, text: item } : item
  );
  const abstract = data?.abstract || '';
  const docName = data?.doc_id ? `Document ${data.doc_id}` : '';

  return (
    <main className="page" id="page-cheatsheet">
      <header className="cheatsheet__header">
        <h1 id="cheatsheet-title">
          <TextScramble text="Cheat Sheet" />
        </h1>
      </header>
      <p className="cheatsheet__doc-name" id="cheatsheet-doc-name">{docName}</p>
      <hr className="cheatsheet__rule" />

      <div className="cheatsheet__layout">
        {/* LEFT — 7 cols */}
        <div id="cheatsheet-left">
          <Flashcard terms={terms} />

          {insights.length > 0 && (
            <section id="key-insights">
              <div className="insights__label">KEY INSIGHTS</div>
              {insights.map((insight, i) => (
                <div className="insight-block stagger-in" key={i} id={`insight-${i}`}>
                  <span className="insight-block__number">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <p className="insight-block__text">
                    {typeof insight === 'string' ? insight : (insight.sentence || insight.text)}
                  </p>
                </div>
              ))}
            </section>
          )}
        </div>

        {/* RIGHT — 5 cols */}
        <div id="cheatsheet-right">
          <div className="section-label">ENTITIES</div>
          <EntityCloud entities={entities} />

          {timeline.length > 0 && <Timeline events={timeline} />}

          {abstract && (
            <section className="abstract" id="abstract-section">
              <div className="abstract__label">ABSTRACT</div>
              <p className="abstract__text">{abstract}</p>
            </section>
          )}
        </div>
      </div>
    </main>
  );
}
