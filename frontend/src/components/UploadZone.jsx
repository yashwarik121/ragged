import { useState, useRef, useEffect, useCallback } from 'react';
import axios from 'axios';

const API = 'http://localhost:8000';

const STAGES = [
  { label: 'EXTRACTING TEXT...', progress: 20 },
  { label: 'CHUNKING...', progress: 40 },
  { label: 'EMBEDDING...', progress: 65 },
  { label: 'ANALYZING ENTITIES...', progress: 85 },
  { label: 'COMPLETE', progress: 100 },
];

export default function UploadZone({ onUploadComplete }) {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [fileName, setFileName] = useState('');
  const [stageIdx, setStageIdx] = useState(0);
  const [dots, setDots] = useState('');
  const inputRef = useRef(null);
  const dotsInterval = useRef(null);

  useEffect(() => {
    if (!uploading) return;
    dotsInterval.current = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 400);
    return () => clearInterval(dotsInterval.current);
  }, [uploading]);

  const simulateStages = useCallback(() => {
    let idx = 0;
    const interval = setInterval(() => {
      idx++;
      if (idx < STAGES.length) {
        setStageIdx(idx);
      } else {
        clearInterval(interval);
      }
    }, 800);
    return interval;
  }, []);

  const handleUpload = useCallback(async (file) => {
    if (!file) return;
    setFileName(file.name);
    setUploading(true);
    setStageIdx(0);

    const stageInterval = simulateStages();

    try {
      const form = new FormData();
      form.append('file', file);
      const res = await axios.post(`${API}/upload`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // Wait for stages to finish visually
      await new Promise(r => setTimeout(r, STAGES.length * 800));
      clearInterval(stageInterval);
      setUploading(false);
      if (onUploadComplete) onUploadComplete(res.data);
    } catch (err) {
      clearInterval(stageInterval);
      setUploading(false);
      console.error('Upload failed:', err);
    }
  }, [onUploadComplete, simulateStages]);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleUpload(file);
  }, [handleUpload]);

  const onDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const onDragLeave = useCallback(() => {
    setDragOver(false);
  }, []);

  const onFileChange = useCallback((e) => {
    const file = e.target.files[0];
    handleUpload(file);
  }, [handleUpload]);

  return (
    <>
      <div
        className={`upload-zone ${dragOver ? 'upload-zone--dragover' : ''}`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => inputRef.current?.click()}
        id="upload-zone"
        role="button"
        tabIndex={0}
        aria-label="Upload document"
      >
        <span className="upload-zone__label">
          DROP PDF HERE — OR CLICK TO BROWSE
        </span>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt,.docx"
          className="upload-zone__input"
          onChange={onFileChange}
          id="upload-input"
        />
      </div>

      {uploading && (
        <div className="upload-overlay" id="upload-overlay">
          <div className="upload-overlay__filename">
            {fileName}{dots}
          </div>
          <div className="upload-overlay__progress-track">
            <div
              className="upload-overlay__progress-bar"
              style={{ width: `${STAGES[stageIdx].progress}%` }}
            />
          </div>
          <div className="upload-overlay__status">
            {STAGES[stageIdx].label}
          </div>
        </div>
      )}
    </>
  );
}
