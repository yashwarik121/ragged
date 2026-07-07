import { useEffect, useRef, useState } from 'react';

const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*<>[]{}';
const RESOLVE_MS = 600;

export default function TextScramble({ text, className = '' }) {
  const [display, setDisplay] = useState('');
  const frameRef = useRef(null);
  const startRef = useRef(null);

  useEffect(() => {
    if (!text) { setDisplay(''); return; }

    const target = text.toUpperCase();
    const len = target.length;
    const resolved = new Array(len).fill(false);
    startRef.current = performance.now();

    function tick(now) {
      const elapsed = now - startRef.current;
      const progress = Math.min(elapsed / RESOLVE_MS, 1);
      const resolvedCount = Math.floor(progress * len);

      const chars = [];
      for (let i = 0; i < len; i++) {
        if (i < resolvedCount || resolved[i]) {
          resolved[i] = true;
          chars.push(target[i]);
        } else if (target[i] === ' ') {
          chars.push(' ');
        } else {
          chars.push(CHARS[Math.floor(Math.random() * CHARS.length)]);
        }
      }
      setDisplay(chars.join(''));

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick);
      }
    }

    frameRef.current = requestAnimationFrame(tick);
    return () => { if (frameRef.current) cancelAnimationFrame(frameRef.current); };
  }, [text]);

  return (
    <span className={`text-scramble ${className}`} aria-label={text}>
      {display}
    </span>
  );
}
