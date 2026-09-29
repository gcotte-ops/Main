export interface MapPoint {
  id: string;
  label: string;
  kind: 'user' | 'archetype' | 'candidate';
  x: number;
  y: number;
  /** Demi-largeurs d'incertitude (IC pour l'utilisateur·ice, confiance du codage pour les candidat·es). */
  ex?: number;
  ey?: number;
  imputed?: boolean;
}

/** Carte 2D (ECO × Ouverture–Fermeture, ou deux premières composantes de l'ACP). Un seul axe par dimension. */
const W = 640;
const H = 520;
const M = { l: 56, r: 24, t: 24, b: 56 };

export function Map2D(props: {
  points: MapPoint[];
  xLabel: [string, string, string];
  yLabel: [string, string, string];
  domain?: number;
  showLabels?: 'all' | 'user-and-candidates';
}) {
  const D = props.domain ?? 100;
  const sx = (v: number) => M.l + ((v + D) / (2 * D)) * (W - M.l - M.r);
  const sy = (v: number) => H - M.b - ((v + D) / (2 * D)) * (H - M.t - M.b);
  const clamp = (v: number) => Math.max(-D, Math.min(D, v));
  const order = { archetype: 0, candidate: 1, user: 2 } as const;
  const pts = [...props.points].sort((a, b) => order[a.kind] - order[b.kind]);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" className="map2d">
      <rect x={M.l} y={M.t} width={W - M.l - M.r} height={H - M.t - M.b} className="plot-bg" />
      {[-0.5, 0.5].map((f) => (
        <g key={f}>
          <line x1={sx(f * D)} x2={sx(f * D)} y1={M.t} y2={H - M.b} className="grid" />
          <line x1={M.l} x2={W - M.r} y1={sy(f * D)} y2={sy(f * D)} className="grid" />
        </g>
      ))}
      <line x1={sx(0)} x2={sx(0)} y1={M.t} y2={H - M.b} className="grid-mid" />
      <line x1={M.l} x2={W - M.r} y1={sy(0)} y2={sy(0)} className="grid-mid" />
      <text x={M.l} y={H - 18} className="chart-label">← {props.xLabel[0]}</text>
      <text x={W - M.r} y={H - 18} textAnchor="end" className="chart-label">{props.xLabel[1]} →</text>
      <text x={(M.l + W - M.r) / 2} y={H - 4} textAnchor="middle" className="chart-tick">{props.xLabel[2]}</text>
      <text x={14} y={H - M.b} transform={`rotate(-90 14 ${H - M.b})`} className="chart-label">← {props.yLabel[0]}</text>
      <text x={14} y={M.t} transform={`rotate(-90 14 ${M.t})`} textAnchor="end" className="chart-label">{props.yLabel[1]} →</text>
      <text x={30} y={(M.t + H - M.b) / 2} transform={`rotate(-90 30 ${(M.t + H - M.b) / 2})`} textAnchor="middle" className="chart-tick">{props.yLabel[2]}</text>
      {pts.map((p) => {
        const cx = sx(clamp(p.x));
        const cy = sy(clamp(p.y));
        const tip = `${p.label} : (${Math.round(p.x)} ; ${Math.round(p.y)})${p.imputed ? ' — axes manquants imputés' : ''}`;
        return (
          <g key={`${p.kind}-${p.id}`} tabIndex={0} aria-label={tip} className="map-point">
            <title>{tip}</title>
            {p.ex !== undefined && (
              <line x1={sx(clamp(p.x - p.ex))} x2={sx(clamp(p.x + p.ex))} y1={cy} y2={cy} className={p.kind === 'user' ? 'whisker-user' : 'whisker'} />
            )}
            {p.ey !== undefined && (
              <line x1={cx} x2={cx} y1={sy(clamp(p.y - p.ey))} y2={sy(clamp(p.y + p.ey))} className={p.kind === 'user' ? 'whisker-user' : 'whisker'} />
            )}
            {p.kind === 'archetype' && <rect x={cx - 5} y={cy - 5} width={10} height={10} rx={2} className="mark-archetype" />}
            {p.kind === 'candidate' && <path d={`M${cx} ${cy - 6} L${cx + 6} ${cy} L${cx} ${cy + 6} L${cx - 6} ${cy} Z`} className={p.imputed ? 'mark-candidate mark-imputed' : 'mark-candidate'} />}
            {p.kind === 'user' && <circle cx={cx} cy={cy} r={8} className="mark-user" />}
            {(props.showLabels === 'all' || p.kind !== 'archetype') && (
              <text x={cx > W * 0.7 ? cx - 9 : cx + 9} y={cy - 7} textAnchor={cx > W * 0.7 ? 'end' : 'start'} className={p.kind === 'user' ? 'chart-label-strong' : 'chart-tick'}>{p.kind === 'user' ? 'Vous' : p.label}</text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
