import type { AxisReading } from '../../engine/narrative';

/** Barres divergentes par axe : pôles à gauche et à droite, zone du centre [−20, 20] ombrée, IC en moustache. */
const W = 760;
const ROW = 38;
const L = 180;
const Rm = 230;
const plotW = W - L - Rm;
const x = (v: number) => L + ((v + 100) / 200) * plotW;

export function DivergingBars({ rows }: { rows: AxisReading[] }) {
  const H = rows.length * ROW + 24;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" className="bars">
      <rect x={x(-20)} y={0} width={x(20) - x(-20)} height={H - 20} className="zone-center" />
      <line x1={x(0)} x2={x(0)} y1={0} y2={H - 20} className="grid-mid" />
      {rows.map((r, i) => {
        const y = i * ROW + 6;
        const s = r.score.score;
        const mid = y + 13;
        return (
          <g key={r.axis.id}>
            <text x={L - 8} y={mid - 5} textAnchor="end" className="chart-label">{r.axis.poleMinus}</text>
            <text x={L - 8} y={mid + 9} textAnchor="end" className="chart-tick">{r.axis.label}</text>
            <PoleLabel x={W - Rm + 8} y={mid - 5} text={r.axis.polePlus} />
            <line x1={L} x2={W - Rm} y1={mid} y2={mid} className="grid" />
            {s !== null && (
              <>
                <rect
                  x={Math.min(x(0), x(s))} y={mid - 7} width={Math.max(2, Math.abs(x(s) - x(0)))} height={14} rx={3}
                  className={r.score.established ? 'bar-user' : 'bar-user bar-weak'}
                >
                  <title>{`${r.axis.label} : ${Math.round(s)}${r.score.ci ? ` (IC ${Math.round(r.score.ci[0])} à ${Math.round(r.score.ci[1])})` : ''}${r.score.established ? '' : ' — position peu établie'}`}</title>
                </rect>
                {r.score.ci && (
                  <line x1={x(r.score.ci[0])} x2={x(r.score.ci[1])} y1={mid} y2={mid} className="whisker" />
                )}
              </>
            )}
          </g>
        );
      })}
      {[-100, -60, -20, 20, 60, 100].map((v) => (
        <text key={v} x={x(v)} y={H - 6} textAnchor="middle" className="chart-tick">{v > 0 ? `+${v}` : v}</text>
      ))}
    </svg>
  );
}

/** Libellé de pôle, coupé avant la parenthèse s'il est trop long pour la marge. */
function PoleLabel({ x, y, text }: { x: number; y: number; text: string }) {
  const k = text.indexOf(' (');
  if (text.length <= 34 || k < 0) return <text x={x} y={y} className="chart-label">{text}</text>;
  return (
    <text x={x} y={y - 4} className="chart-label">
      <tspan x={x}>{text.slice(0, k)}</tspan>
      <tspan x={x} dy="1.1em" className="chart-tick">{text.slice(k + 1)}</tspan>
    </text>
  );
}
