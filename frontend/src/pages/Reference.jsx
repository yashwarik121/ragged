import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import TextScramble from '../components/TextScramble';
import CitationBlock from '../components/CitationBlock';
import ExportButton from '../components/ExportButton';

const API = 'http://localhost:8000';

export default function Reference({ setDocInfo }) {
  const { docId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await axios.get(`${API}/reference/${docId}`);
        setData(res.data);
        setDocInfo({ id: docId, name: res.data.document_name || res.data.title || docId });
        setError(null);
      } catch (err) {
        console.error('Failed to fetch reference:', err);
        setError('FAILED TO LOAD REFERENCE DATA');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [docId]);

  if (loading) {
    return (
      <main className="page" id="page-reference">
        <div className="loading-bar"><div className="loading-bar__inner" /></div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page" id="page-reference">
        <div className="state-message state-message--error">{error}</div>
      </main>
    );
  }

  const claims = data?.claims || [];
  const statistics = data?.statistics || [];
  const evidence = data?.evidence_passages || [];
  // Compute unique pages cited across all chunks
  const allPages = new Set([
    ...claims.map(c => c.page),
    ...statistics.map(s => s.page),
    ...evidence.map(e => e.page),
  ].filter(p => p != null));
  const stats = {
    claims: claims.length,
    statistics: statistics.length,
    pages: allPages.size,
    passages: evidence.length,
  };

  return (
    <main className="page" id="page-reference">
      <header>
        <h1 id="reference-title">
          <TextScramble text="Reference" />
        </h1>
      </header>

      {/* Stats Bar */}
      <div className="reference__stats-bar" id="reference-stats">
        <div className="stat-cell stagger-in">
          <div className="stat-cell__number">{stats.claims}</div>
          <div className="stat-cell__label">Claims Found</div>
        </div>
        <div className="stat-cell stagger-in">
          <div className="stat-cell__number">{stats.statistics}</div>
          <div className="stat-cell__label">Statistics</div>
        </div>
        <div className="stat-cell stagger-in">
          <div className="stat-cell__number">{stats.pages}</div>
          <div className="stat-cell__label">Pages Cited</div>
        </div>
        <div className="stat-cell stagger-in">
          <div className="stat-cell__number">{stats.passages}</div>
          <div className="stat-cell__label">Passages</div>
        </div>
      </div>

      {/* Three-Column Layout */}
      <div className="reference__columns" id="reference-columns">
        {/* Column 1 — Claims */}
        <div id="claims-column">
          <div className="reference__column-header">CLAIMS</div>
          {claims.length === 0 && (
            <div className="state-message">NO CLAIMS EXTRACTED</div>
          )}
          {claims.map((c, i) => (
            <CitationBlock
              key={i}
              claim={c.sentence}
              source={`[P.${String(c.page || '?').padStart(2, '0')}]`}
              passage={c.sentence}
            />
          ))}
        </div>

        {/* Column 2 — Statistics */}
        <div id="statistics-column">
          <div className="reference__column-header">STATISTICS</div>
          {statistics.length === 0 && (
            <div className="state-message">NO STATISTICS FOUND</div>
          )}
          {statistics.map((s, i) => {
            // Extract the first number/percentage from the sentence for the big display
            const numMatch = s.sentence?.match(/(\d+(?:\.\d+)?%|\$[\d,.]+|[\d,]+(?:\.\d+)?\s*(?:million|billion|trillion|thousand)?)/i);
            const displayNum = numMatch ? numMatch[0] : '—';
            return (
              <div className="ref-stat stagger-in" key={i} id={`stat-${i}`}>
                <div className="ref-stat__number">{displayNum}</div>
                <div className="ref-stat__context">{s.sentence}</div>
                <div className="ref-stat__page">P.{String(s.page || '?').padStart(2, '0')}</div>
              </div>
            );
          })}
        </div>

        {/* Column 3 — Evidence */}
        <div id="evidence-column">
          <div className="reference__column-header">EVIDENCE</div>
          {evidence.length === 0 && (
            <div className="state-message">NO EVIDENCE PASSAGES</div>
          )}
          {evidence.map((e, i) => (
            <div className="evidence-box stagger-in" key={i} id={`evidence-${i}`}>
              <span className="evidence-box__page">P.{String(e.page || '?').padStart(2, '0')}</span>
              <p className="evidence-box__text">{e.text || e.passage}</p>
            </div>
          ))}
        </div>
      </div>

      <ExportButton docId={docId} />
    </main>
  );
}
