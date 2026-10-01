import type { AxisId, Tension } from '../domain/schemas';
import type { Scores } from './scoring';

/**
 * Indices de cohérence idéologique (docs/METHODOLOGIE.md §6). Ils décrivent des combinaisons de positions
 * documentées par la littérature ; ils ne notent personne. Chaque composante est orientée de sorte que
 * +100 = pôle caractéristique du courant ; l'indice est la moyenne des composantes disponibles et
 * « marqué » si toutes dépassent +30.
 */
export interface IdeologicalIndex {
  id: 'intersectionnalite' | 'fusionnisme' | 'souverainisme-social';
  value: number | null;
  marked: boolean;
  components: { axis: AxisId; sign: 1 | -1; value: number | null }[];
}

const DEFS: Record<IdeologicalIndex['id'], { axis: AxisId; sign: 1 | -1; optional?: boolean }[]> = {
  // Crenshaw, Hill Collins, Fraser : convergence ALT, (GEN), ECO, CUL vers les pôles égalitaires.
  intersectionnalite: [{ axis: 'ALT', sign: 1 }, { axis: 'GEN', sign: 1, optional: true }, { axis: 'ECO', sign: 1 }, { axis: 'CUL', sign: 1 }],
  // Fusionnisme / libéral-conservatisme : ECO néolibéral × CUL conservateur × REL traditionnel.
  fusionnisme: [{ axis: 'ECO', sign: -1 }, { axis: 'CUL', sign: -1 }, { axis: 'REL', sign: 1 }],
  // Souverainisme social : ECO socialiste × ETA et UE nationaux.
  'souverainisme-social': [{ axis: 'ECO', sign: 1 }, { axis: 'ETA', sign: -1 }, { axis: 'UE', sign: -1 }],
};

export function computeIndices(scores: Scores): IdeologicalIndex[] {
  return (Object.keys(DEFS) as IdeologicalIndex['id'][]).map((id) => {
    const components = DEFS[id]
      .map((d) => {
        const s = scores[d.axis]?.score;
        return { axis: d.axis, sign: d.sign, value: s === null || s === undefined ? null : d.sign * s, optional: d.optional };
      })
      .filter((c) => c.value !== null || !c.optional)
      .map(({ axis, sign, value }) => ({ axis, sign, value }));
    const vals = components.map((c) => c.value).filter((v): v is number => v !== null);
    const complete = vals.length === components.length;
    const value = complete && vals.length ? Math.round(vals.reduce((s, v) => s + v, 0) / vals.length) : null;
    return { id, value, marked: complete && vals.every((v) => v > 30), components };
  });
}

/** Règles de tension : toutes les conditions doivent être vérifiées sur des dimensions mesurées. */
export function detectTensions(scores: Scores, tensions: Tension[], max = 3): Tension[] {
  const hits = tensions
    .map((t) => {
      let margin = Infinity;
      for (const c of t.when) {
        const s = scores[c.axis as keyof Scores]?.score;
        if (s === null || s === undefined) return null;
        const m = c.op === '<' ? c.value - s : s - c.value;
        if (m <= 0) return null;
        margin = Math.min(margin, m);
      }
      return { t, margin };
    })
    .filter((x): x is { t: Tension; margin: number } => x !== null)
    .sort((a, b) => b.margin - a.margin);
  return hits.slice(0, max).map((h) => h.t);
}

/**
 * Indice composite « Ouverture–Fermeture » (ordonnée de la carte 2D) :
 * moyenne pondérée de CUL, ALT, GOV, ETA (poids documentés dans la Méthodologie).
 */
export const OPENNESS_WEIGHTS: Partial<Record<AxisId, number>> = { CUL: 0.3, ALT: 0.3, GOV: 0.2, ETA: 0.2 };

export function opennessIndex(v: Partial<Record<AxisId, number | null>>): number | null {
  let num = 0, den = 0;
  for (const [axis, w] of Object.entries(OPENNESS_WEIGHTS) as [AxisId, number][]) {
    const x = v[axis];
    if (x === null || x === undefined) continue;
    num += w * x;
    den += w;
  }
  return den >= 0.5 ? Math.round((num / den) * 10) / 10 : null;
}
