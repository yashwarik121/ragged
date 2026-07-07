import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import TextScramble from '../components/TextScramble';
import ConfidenceMeter from '../components/ConfidenceMeter';

const API = 'http://localhost:8000';

export default function Report({ setDocInfo }) {
  const { docId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [needsGeneration, setNeedsGeneration] = useState(false);

  const fetchReport = async () => {
    try {
      setLoading(true);
      // Try posting — the backend creates or returns existing report
      const res = await axios.post(`${API}/report`, { doc_id: docId });
      setData(res.data);
      setDocInfo({ id: docId, name: res.data.document_name || res.data.title || docId });
      setNeedsGeneration(false);
      setError(null);
    } catch (err) {
      if (err.response?.status === 404) {
        setNeedsGeneration(true);
      } else {
        console.error('Failed to fetch report:', err);
        setError('FAILED TO LOAD REPORT');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [docId]);

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      const res = await axios.post(`${API}/report`, { doc_id: docId });
      setData(res.data);
      setDocInfo({ id: docId, name: res.data.document_name || res.data.title || docId });
      setNeedsGeneration(false);
    } catch (err) {
      console.error('Failed to generate report:', err);
      setError('REPORT GENERATION FAILED');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <main className="page" id="page-report">
        <div className="loading-bar"><div className="loading-bar__inner" /></div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page" id="page-report">
        <div className="state-message state-message--error">{error}</div>
      </main>
    );
  }

  if (needsGeneration || !data) {
    return (
      <main className="page" id="page-report">
        <header>
          <h1 id="report-title">
            <TextScramble text="Opinion" />
          </h1>
        </header>
        <hr className="report__rule" />
        <div className="state-message">
          NO REPORT GENERATED YET
        </div>
        <button
          className="generate-btn"
          onClick={handleGenerate}
          disabled={generating}
          id="generate-report-btn"
        >
          {generating ? 'GENERATING...' : 'GENERATE REPORT'}
        </button>
      </main>
    );
  }

  const confidence = data.confidence_score || 0;
  const brief = data.executive_brief || '';
  const soWhat = data.so_what || '';
  const counterpoint = data.dissenting_opinion || '';

  // Parse critical_analysis — backend returns {text: "..."} or a plain string
  const analysisRaw = typeof data.critical_analysis === 'string'
    ? data.critical_analysis
    : data.critical_analysis?.text || '';

  // Try to split into strengths and weaknesses by looking for section markers
  let strengths = data.strengths || [];
  let weaknesses = data.weaknesses || [];

  if (strengths.length === 0 && weaknesses.length === 0 && analysisRaw) {
    const lines = analysisRaw.split(/\n/).map(l => l.trim()).filter(Boolean);
    let section = 'strengths';
    for (const line of lines) {
      if (/weakness|weak|limitation|concern|gap|missing/i.test(line) && !/^[-•+]/.test(line)) {
        section = 'weaknesses';
        continue;
      }
      if (/strength|strong|robust|thorough|solid/i.test(line) && !/^[-•+]/.test(line)) {
        section = 'strengths';
        continue;
      }
      const cleanLine = line.replace(/^[-•+*]\s*/, '').trim();
      if (cleanLine) {
        if (section === 'strengths') strengths.push(cleanLine);
        else weaknesses.push(cleanLine);
      }
    }
    // Fallback: if we couldn't split, put everything in strengths
    if (strengths.length === 0 && weaknesses.length === 0) {
      strengths = [analysisRaw];
    }
  }

  return (
    <main className="page" id="page-report">
      {/* Header */}
      <header className="report__header">
        <h1 className="report__title" id="report-title">
          <TextScramble text="Opinion" />
        </h1>
        <ConfidenceMeter value={confidence} />
      </header>
      <hr className="report__rule" />

      {/* The Brief */}
      <section id="report-brief">
        <div className="report__section-label">THE BRIEF</div>
        <p className="report__brief-text">{brief}</p>
      </section>

      {/* Analysis — Strengths & Weaknesses */}
      <section id="report-analysis">
        <div className="report__section-label">ANALYSIS</div>
        <div className="report__analysis">
          <div className="report__analysis-col" id="strengths-col">
            <div className="report__section-label">STRENGTHS</div>
            {strengths.map((item, i) => (
              <div className="report__analysis-item stagger-in" key={i} id={`strength-${i}`}>
                <span className="report__analysis-prefix">+</span>
                <span>{typeof item === 'string' ? item : item.text}</span>
              </div>
            ))}
            {strengths.length === 0 && (
              <div className="state-message">—</div>
            )}
          </div>

          <div className="report__analysis-divider" />

          <div className="report__analysis-col" id="weaknesses-col">
            <div className="report__section-label">WEAKNESSES</div>
            {weaknesses.map((item, i) => (
              <div className="report__analysis-item stagger-in" key={i} id={`weakness-${i}`}>
                <span className="report__analysis-prefix">−</span>
                <span>{typeof item === 'string' ? item : item.text}</span>
              </div>
            ))}
            {weaknesses.length === 0 && (
              <div className="state-message">—</div>
            )}
          </div>
        </div>
      </section>

      {/* So What */}
      {soWhat && (
        <section id="report-so-what">
          <div className="report__section-label">SO WHAT</div>
          <div className="report__so-what">
            <p className="report__so-what-text">{soWhat}</p>
          </div>
        </section>
      )}

      {/* Counterpoint */}
      {counterpoint && (
        <section className="report__counterpoint" id="report-counterpoint">
          <div className="report__counterpoint-label">COUNTERPOINT</div>
          <p className="report__counterpoint-text">{counterpoint}</p>
        </section>
      )}
    </main>
  );
}
