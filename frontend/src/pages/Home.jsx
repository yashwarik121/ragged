import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import UploadZone from '../components/UploadZone';

const API = 'http://localhost:8000';

function AnimatedCounter({ target }) {
  const [display, setDisplay] = useState(0);
  const frameRef = useRef(null);
  const startRef = useRef(null);
  const DURATION = 1400;

  useEffect(() => {
    startRef.current = performance.now();

    function tick(now) {
      const elapsed = now - startRef.current;
      const progress = Math.min(elapsed / DURATION, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(eased * target));

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick);
      }
    }

    frameRef.current = requestAnimationFrame(tick);
    return () => { if (frameRef.current) cancelAnimationFrame(frameRef.current); };
  }, [target]);

  return String(display).padStart(3, '0');
}

function formatTime(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  const day = String(d.getDate()).padStart(2, '0');
  const mon = d.toLocaleString('en', { month: 'short' }).toUpperCase();
  const yr = d.getFullYear();
  const h = String(d.getHours()).padStart(2, '0');
  const m = String(d.getMinutes()).padStart(2, '0');
  return `${day} ${mon} ${yr} ${h}:${m}`;
}

export default function Home({ setDocInfo }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const fetchDocs = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/documents`);
      setDocs(res.data || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
      setError('FAILED TO LOAD DOCUMENTS');
      setDocs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
    setDocInfo({ id: null, name: null });
  }, []);

  const handleUploadComplete = (data) => {
    fetchDocs();
  };

  const handleDocClick = (doc) => {
    setDocInfo({ id: doc.id, name: doc.filename });
    navigate(`/cheatsheet/${doc.id}`);
  };

  return (
    <main className="page" id="page-home">
      <header>
        <div className="home__counter" id="doc-counter">
          <span className="home__counter-number">
            <AnimatedCounter target={docs.length} />
          </span>{' '}
          DOCUMENTS ANALYZED
        </div>
        <p className="home__tagline">
          drop your pdfs. get the brain.
        </p>
      </header>

      <section className="home__upload-section" id="upload-section">
        <UploadZone onUploadComplete={handleUploadComplete} />
      </section>

      <section id="doc-library">
        <div className="doc-library__header">DOCUMENT LIBRARY</div>

        {loading && (
          <div className="loading-bar" id="loading-bar">
            <div className="loading-bar__inner" />
          </div>
        )}

        {error && (
          <div className="state-message state-message--error" id="error-message">
            {error}
          </div>
        )}

        {!loading && !error && docs.length === 0 && (
          <div className="state-message" id="empty-message">
            NO DOCUMENTS YET — UPLOAD YOUR FIRST PDF
          </div>
        )}

        {!loading && docs.map((doc, i) => (
          <div
            className="doc-row stagger-in"
            key={doc.id}
            onClick={() => handleDocClick(doc)}
            role="button"
            tabIndex={0}
            id={`doc-row-${doc.id}`}
            onKeyDown={(e) => e.key === 'Enter' && handleDocClick(doc)}
          >
            <span className="doc-row__name">{doc.filename}</span>
            <span className="doc-row__pages">{doc.total_pages || '—'} pg</span>
            <span className="doc-row__time">{formatTime(doc.upload_time)}</span>
            <span className={`doc-row__status doc-row__status--${(doc.status || 'ready').toLowerCase()}`}>
              [{(doc.status || 'READY').toUpperCase()}]
            </span>
          </div>
        ))}
      </section>
    </main>
  );
}
