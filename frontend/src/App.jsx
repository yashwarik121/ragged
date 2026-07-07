import { useState, useCallback, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import Home from './pages/Home';
import CheatSheet from './pages/CheatSheet';
import Reference from './pages/Reference';
import Report from './pages/Report';

export default function App() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('ragged-theme');
    return saved || 'light';
  });

  const [docInfo, setDocInfo] = useState({ id: null, name: null });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ragged-theme', theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  }, []);

  const updateDocInfo = useCallback((info) => {
    setDocInfo(info);
  }, []);

  return (
    <BrowserRouter>
      <Navigation
        docName={docInfo.name}
        docId={docInfo.id}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
      <Routes>
        <Route path="/" element={<Home setDocInfo={updateDocInfo} />} />
        <Route path="/cheatsheet/:docId" element={<CheatSheet setDocInfo={updateDocInfo} />} />
        <Route path="/reference/:docId" element={<Reference setDocInfo={updateDocInfo} />} />
        <Route path="/report/:docId" element={<Report setDocInfo={updateDocInfo} />} />
      </Routes>
    </BrowserRouter>
  );
}
