import type { Axis, AxisId } from '../../domain/schemas';
import type { Scores } from '../../engine/scoring';

/**
 * Carte des intersections (10 × 10) : pour chaque paire d'axes, l'intensité est min(|s_i|, |s_j|)
 * (les deux positions doivent être marquées) ; une combinaison nommée par la littérature est signalée.
 * Échelle séquentielle à une teinte (bleu clair → bleu foncé), 5 classes.
 */
export interface NamedCombo { a: AxisId; sa: 1 | -1; b: AxisId; sb: 1 | -1; name: string; ref: string }

export const NAMED_COMBOS: NamedCombo[] = [
  { a: 'ECO', sa: 1, b: 'ETA', sb: -1, name: 'Souverainisme social', ref: 'Polanyi, List' },
  { a: 'ECO', sa: -1, b: 'CUL', sb: -1, name: 'Libéral-conservatisme (fusionnisme)', ref: 'Burke, Hayek ; critique : Michéa' },
  { a: 'ECO', sa: -1, b: 'CUL', sb: 1, name: 'Libéral-libertaire', ref: 'Boltanski et Chiapello' },
  { a: 'ECO', sa: 1, b: 'ENV', sb: 1, name: 'Écosocialisme', ref: 'Gorz, Malm, Saito' },
  { a: 'ECO', sa: 1, b: 'CUL', sb: 1, name: 'Gauche sociale et culturelle', ref: 'Fraser' },
  { a: 'ECO', sa: 1, b: 'CUL', sb: -1, name: 'Socialisme conservateur (« common decency »)', ref: 'Michéa, Lasch' },
  { a: 'ECO', sa: 1, b: 'GOV', sb: -1, name: 'Étatisme autoritaire de gauche', ref: 'Arendt, Linz' },
  { a: 'ECO', sa: -1, b: 'GOV', sb: -1, name: 'Libéralisme autoritaire', ref: 'Hayek (débat), Schmitt' },
  { a: 'ECO', sa: -1, b: 'GMO', sb: 1, name: 'Libertarianisme non interventionniste', ref: 'Nozick, Rothbard' },
  { a: 'ALT', sa: 1, b: 'CUL', sb: 1, name: 'Progressisme culturel', ref: 'Crenshaw, Fraser' },
  { a: 'ALT', sa: -1, b: 'ETA', sb: -1, name: 'Nationalisme', ref: 'Barrès ; critique : Renan' },
  { a: 'ALT', sa: -1, b: 'CUL', sb: -1, name: 'Conservatisme identitaire', ref: 'Benoist ; critique : Taguieff' },
  { a: 'ALT', sa: 1, b: 'REL', sb: 1, name: 'Christianisme social d\'accueil', ref: 'Doctrine sociale de l\'Église' },
  { a: 'REL', sa: 1, b: 'CUL', sb: -1, name: 'Traditionalisme', ref: 'Maistre, MacIntyre' },
  { a: 'REL', sa: -1, b: 'CUL', sb: 1, name: 'Laïcité émancipatrice', ref: 'Voltaire, Peña-Ruiz' },
  { a: 'IDE', sa: 1, b: 'ALT', sb: 1, name: 'Politique de la reconnaissance', ref: 'Taylor, Kymlicka' },
  { a: 'IDE', sa: -1, b: 'ALT', sb: 1, name: 'Universalisme républicain', ref: 'Schnapper, Mounk' },
  { a: 'IDE', sa: 1, b: 'ETA', sb: -1, name: 'Enracinement national', ref: 'Barrès, Scruton' },
  { a: 'ETA', sa: 1, b: 'UE', sb: 1, name: 'Fédéralisme cosmopolite', ref: 'Kant, Habermas' },
  { a: 'ETA', sa: -1, b: 'UE', sb: -1, name: 'Souverainisme', ref: 'Séguin, De Gaulle' },
  { a: 'ETA', sa: 1, b: 'UE', sb: -1, name: 'Internationalisme critique de l\'UE', ref: 'Lordon, Streeck' },
  { a: 'UE', sa: 1, b: 'GMO', sb: -1, name: 'Europe puissance', ref: 'Kagan (débat), Aron' },
  { a: 'UE', sa: 1, b: 'GMO', sb: 1, name: 'Europe puissance civile', ref: 'Monnet, Habermas' },
  { a: 'ENV', sa: 1, b: 'CUL', sb: -1, name: 'Écologie enracinée', ref: 'Laudato si\', Scruton' },
  { a: 'ENV', sa: 1, b: 'GOV', sb: -1, name: 'Écologie autoritaire', ref: 'Linkola (repoussoir), Jonas (débat)' },
  { a: 'GOV', sa: 1, b: 'CUL', sb: 1, name: 'Libéralisme politique et culturel', ref: 'Mill, Constant' },
  { a: 'GOV', sa: -1, b: 'CUL', sb: -1, name: 'Autoritarisme conservateur', ref: 'Altemeyer, Stenner' },
  { a: 'GMO', sa: -1, b: 'GOV', sb: 1, name: 'Interventionnisme démocratique', ref: 'Walzer, R2P' },
];

const CLASSES = ['heat-0', 'heat-1', 'heat-2', 'heat-3', 'heat-4'];

export function comboFor(a: AxisId, b: AxisId, sa: number, sb: number): NamedCombo | undefined {
  return NAMED_COMBOS.find((c) => (c.a === a && c.b === b && Math.sign(sa) === c.sa && Math.sign(sb) === c.sb) || (c.a === b && c.b === a && Math.sign(sb) === c.sa && Math.sign(sa) === c.sb));
}

export function intersectionCells(axes: Axis[], scores: Scores) {
  const cells: { i: number; j: number; a: Axis; b: Axis; value: number; combo?: NamedCombo }[] = [];
  axes.forEach((a, i) => axes.forEach((b, j) => {
    if (j <= i) return;
    const sa = scores[a.id]?.score ?? null;
    const sb = scores[b.id]?.score ?? null;
    if (sa === null || sb === null) return;
    const value = Math.min(Math.abs(sa), Math.abs(sb));
    cells.push({ i, j, a, b, value, combo: value >= 30 ? comboFor(a.id, b.id, sa, sb) : undefined });
  }));
  return cells;
}

export function Heatmap({ axes, scores }: { axes: Axis[]; scores: Scores }) {
  const n = axes.length;
  const S = 44;
  const L = 60;
  const T = 60;
  const W = L + n * S + 8;
  const cells = intersectionCells(axes, scores);
  return (
    <svg viewBox={`0 0 ${W} ${T + n * S + 8}`} width="100%" style={{ maxWidth: W }} className="heatmap">
      {axes.map((a, k) => (
        <g key={a.id}>
          <text x={L - 6} y={T + k * S + S / 2} textAnchor="end" dominantBaseline="middle" className="chart-label">{a.id}</text>
          <text x={L + k * S + S / 2} y={T - 8} textAnchor="middle" className="chart-label">{a.id}</text>
        </g>
      ))}
      {cells.map((c) => {
        const k = Math.min(4, Math.floor(c.value / 20));
        const tip = `${c.a.label} × ${c.b.label} : intensité ${Math.round(c.value)}${c.combo ? ` — ${c.combo.name} (${c.combo.ref})` : ''}`;
        return (
          <g key={`${c.i}-${c.j}`}>
            {/* Triangle supérieur : (ligne i, colonne j) ; case miroir en dessous. */}
            {[[c.i, c.j], [c.j, c.i]].map(([r, col]) => (
              <rect key={`${r}-${col}`} x={L + col! * S + 1} y={T + r! * S + 1} width={S - 2} height={S - 2} rx={3} className={CLASSES[k]}>
                <title>{tip}</title>
              </rect>
            ))}
            {c.combo && <circle cx={L + c.j * S + S / 2} cy={T + c.i * S + S / 2} r={5} className="mark-user"><title>{tip}</title></circle>}
          </g>
        );
      })}
      {axes.map((a, k) => <rect key={a.id} x={L + k * S + 1} y={T + k * S + 1} width={S - 2} height={S - 2} rx={3} className="heat-diag" />)}
    </svg>
  );
}
