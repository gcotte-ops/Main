import { useId, useRef, useState, type ReactNode } from 'react';
import { exportNodePng } from '../exporting';

/**
 * Cadre commun des graphiques : titre (Fraunces), légende (Open Sans), tableau équivalent accessible
 * et export PNG. Le graphique SVG est décrit par aria-labelledby ; le tableau porte les données.
 */
export function ChartFrame(props: {
  title: string;
  description: string;
  legend?: ReactNode;
  table: ReactNode;
  controls?: ReactNode;
  fileName: string;
  children: ReactNode;
}) {
  const id = useId();
  const ref = useRef<HTMLDivElement>(null);
  const [busy, setBusy] = useState(false);
  return (
    <figure className="chart" aria-labelledby={`${id}-t`}>
      <div ref={ref} className="chart-capture">
        <h3 id={`${id}-t`}>{props.title}</h3>
        <p id={`${id}-d`} className="small muted">{props.description}</p>
        {props.controls && <div className="chart-controls">{props.controls}</div>}
        <div className="chart-plot" role="img" aria-labelledby={`${id}-t ${id}-d`}>{props.children}</div>
        {props.legend && <div className="chart-legend small">{props.legend}</div>}
      </div>
      <details className="chart-table">
        <summary>Afficher le tableau de données</summary>
        {props.table}
      </details>
      <button
        type="button"
        className="btn btn-small"
        disabled={busy}
        onClick={async () => {
          if (!ref.current) return;
          setBusy(true);
          try { await exportNodePng(ref.current, props.fileName); } finally { setBusy(false); }
        }}
      >
        Exporter en PNG
      </button>
    </figure>
  );
}

export function LegendItem({ shape, label }: { shape: 'user' | 'archetype' | 'candidate' | 'ci'; label: string }) {
  return (
    <span className="legend-item">
      <svg width="14" height="14" aria-hidden="true" viewBox="-7 -7 14 14">
        {shape === 'user' && <circle r="5" className="mark-user" />}
        {shape === 'archetype' && <rect x="-4.5" y="-4.5" width="9" height="9" rx="1.5" className="mark-archetype" />}
        {shape === 'candidate' && <path d="M0 -5.5 L5.5 0 L0 5.5 L-5.5 0 Z" className="mark-candidate" />}
        {shape === 'ci' && <rect x="-6" y="-3" width="12" height="6" className="mark-ci" />}
      </svg>
      {label}
    </span>
  );
}
