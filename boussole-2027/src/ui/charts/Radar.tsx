import type { Axis } from '../../domain/schemas';
import type { AxisScore } from '../../engine/scoring';

/**
 * Radar : rayon 0 = −100 (pôle « moins »), cercle médian = 0, bord = +100 (pôle « plus »).
 * Zone utilisateur en jaune (contour bleu foncé pour le contraste), intervalle de confiance en halo.
 */
const SIZE = 440;
const PAD = 90; // marge latérale pour les libellés longs
const R = 150;
const C = SIZE / 2;

const rad = (v: number) => ((v + 100) / 200) * R;
const pt = (i: number, n: number, v: number): [number, number] => {
  const a = (Math.PI * 2 * i) / n - Math.PI / 2;
  return [C + rad(v) * Math.cos(a), C + rad(v) * Math.sin(a)];
};
const poly = (vals: number[]) => vals.map((v, i) => pt(i, vals.length, v).map((x) => x.toFixed(1)).join(',')).join(' ');

export function Radar({ axes, scores }: { axes: Axis[]; scores: Partial<Record<string, AxisScore>> }) {
  const n = axes.length;
  const val = axes.map((a) => scores[a.id]?.score ?? 0);
  const lo = axes.map((a) => scores[a.id]?.ci?.[0] ?? scores[a.id]?.score ?? 0);
  const hi = axes.map((a) => scores[a.id]?.ci?.[1] ?? scores[a.id]?.score ?? 0);
  const ring = (v: number) => poly(axes.map(() => v));
  // Halo d'incertitude : couronne entre la borne haute et la borne basse (règle evenodd).
  const halo = `M${poly(hi).split(' ').join(' L')} Z M${poly(lo).split(' ').reverse().join(' L')} Z`;
  return (
    <svg viewBox={`${-PAD} 0 ${SIZE + 2 * PAD} ${SIZE}`} width="100%" style={{ maxWidth: SIZE + 2 * PAD }} className="radar">
      {[-100, -50, 0, 50, 100].map((v) => (
        <polygon key={v} points={ring(v)} className={v === 0 ? 'grid-mid' : 'grid'} />
      ))}
      {axes.map((a, i) => {
        const [x, y] = pt(i, n, 100);
        return <line key={a.id} x1={C} y1={C} x2={x} y2={y} className="grid" />;
      })}
      <path d={halo} className="mark-ci" fillRule="evenodd" />
      <polygon points={poly(val)} className="radar-user" />
      {axes.map((a, i) => {
        const s = scores[a.id];
        const [x, y] = pt(i, n, val[i]!);
        return (
          <circle key={a.id} cx={x} cy={y} r={5} className="mark-user">
            <title>{`${a.label} : ${s?.score === null || s?.score === undefined ? 'non mesuré' : Math.round(s.score)}${s?.ci ? ` (IC ${Math.round(s.ci[0])} à ${Math.round(s.ci[1])})` : ''}`}</title>
          </circle>
        );
      })}
      {axes.map((a, i) => {
        const [x, y] = pt(i, n, 128);
        const anchor = Math.abs(x - C) < 10 ? 'middle' : x > C ? 'start' : 'end';
        return (
          <text key={a.id} x={x} y={y} textAnchor={anchor} dominantBaseline="middle" className="chart-label">
            <tspan x={x} className="chart-label-strong">{a.id}</tspan>
            <tspan x={x} dy="1.15em">{a.label}</tspan>
          </text>
        );
      })}
      <text x={C + 4} y={C - rad(0) + 11} className="chart-tick">0</text>
      <text x={C + 4} y={C - rad(-100) + 11} className="chart-tick">−100</text>
    </svg>
  );
}
