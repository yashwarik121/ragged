import { useEffect, useRef, useState } from 'react';

export default function ConfidenceMeter({ value = 0, label }) {
  const [display, setDisplay] = useState(0);
  const frameRef = useRef(null);
  const startRef = useRef(null);
  const DURATION = 1200;

  useEffect(() => {
    startRef.current = performance.now();

    function tick(now) {
      const elapsed = now - startRef.current;
      const progress = Math.min(elapsed / DURATION, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(eased * value));

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick);
      }
    }

    frameRef.current = requestAnimationFrame(tick);
    return () => { if (frameRef.current) cancelAnimationFrame(frameRef.current); };
  }, [value]);

  return (
    <div className="confidence-meter" id="confidence-meter">
      <div className="confidence-meter__value" aria-label={`${value}% confidence`}>
        {display}%
      </div>
      {label && <div className="confidence-meter__label">{label}</div>}
    </div>
  );
}
