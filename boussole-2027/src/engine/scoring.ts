import type { Answer, Answers, AxisId, Question } from '../domain/schemas';
import { mulberry32 } from './rng';

/**
 * Formule (docs/METHODOLOGIE.md §3) : chaque item répondu apporte, pour chaque axe a qu'il charge,
 * un couple (contribution n, maximum m). S_a = 100 · Σ n / Σ m ∈ [−100, 100].
 *  - Likert r ∈ {−2..+2}, poids w : n = w·r, m = 2|w|  (≡ Σ w·r / (2 Σ|w|) de la spécification).
 *  - Dilemme v ∈ {−2..+2} (−2 = « A nettement », +2 = « B nettement », 0 = « les deux se valent ») :
 *    n = |v|·w(option choisie), m = 2·max(|w_A|, |w_B|).
 *  - Allocation (parts s_o, k options) : n = 2·Σ (s_o − 1/k)·w_o, m = 2·max_o |w_o − moyenne(w)| ;
 *    une répartition uniforme est neutre.
 *  - « Sans avis » (null) : item exclu.
 */
export interface Contribution { itemId: string; n: number; m: number }

export type Dimension = AxisId | `${AxisId}.${string}`;

export interface AxisScore {
  /** −100..+100, null si aucun item répondu. */
  score: number | null;
  /** Intervalle de confiance à 95 % (bootstrap sur les items). */
  ci: [number, number] | null;
  nItems: number;
  /** Nombre effectif d'items (Kish) : (Σm)² / Σm². */
  nEff: number;
  /** Faux si nEff < 4 : « position peu établie ». */
  established: boolean;
}

export type Scores = Partial<Record<Dimension, AxisScore>>;

export const MIN_EFFECTIVE_ITEMS = 4;
export const BOOTSTRAP_DRAWS = 500;

function add(map: Map<string, Contribution[]>, dim: string, c: Contribution) {
  if (c.m <= 0) return;
  const list = map.get(dim);
  if (list) list.push(c);
  else map.set(dim, [c]);
}

/** Contributions d'une réponse, par dimension (axe ou facette). */
export function contributions(q: Question, a: Answer | undefined): Map<string, Contribution> {
  const out = new Map<string, Contribution>();
  if (!a) return out;
  if (q.type === 'likert' && a.kind === 'scale' && a.value !== null) {
    for (const [axis, w] of Object.entries(q.loadings ?? {})) out.set(axis, { itemId: q.id, n: w! * a.value, m: 2 * Math.abs(w!) });
    if (q.facet && q.facetLoading) out.set(q.facet, { itemId: q.id, n: q.facetLoading * a.value, m: 2 * Math.abs(q.facetLoading) });
  } else if (q.type === 'dilemma' && a.kind === 'scale' && a.value !== null) {
    const [A, B] = q.options!;
    const axes = new Set([...Object.keys(A!.loadings), ...Object.keys(B!.loadings)]) as Set<AxisId>;
    const chosen = a.value < 0 ? A! : B!;
    for (const axis of axes) {
      const m = 2 * Math.max(Math.abs(A!.loadings[axis] ?? 0), Math.abs(B!.loadings[axis] ?? 0));
      out.set(axis, { itemId: q.id, n: Math.abs(a.value) * (chosen.loadings[axis] ?? 0), m });
    }
    // Facette d'un dilemme : facetLoading s'applique dans le sens de l'option B (v > 0).
    if (q.facet && q.facetLoading) out.set(q.facet, { itemId: q.id, n: q.facetLoading * a.value, m: 2 * Math.abs(q.facetLoading) });
  } else if (q.type === 'allocation' && a.kind === 'allocation') {
    const opts = q.options!;
    const total = a.points.reduce((s, p) => s + p, 0);
    if (total <= 0) return out;
    const k = opts.length;
    const axes = new Set(opts.flatMap((o) => Object.keys(o.loadings))) as Set<AxisId>;
    for (const axis of axes) {
      const w = opts.map((o) => o.loadings[axis] ?? 0);
      const mean = w.reduce((s, x) => s + x, 0) / k;
      const n = 2 * w.reduce((s, wo, i) => s + ((a.points[i] ?? 0) / total - 1 / k) * wo, 0);
      const m = 2 * Math.max(...w.map((wo) => Math.abs(wo - mean)));
      out.set(axis, { itemId: q.id, n, m });
    }
  }
  return out;
}

function ratio(cs: Contribution[]): number {
  const m = cs.reduce((s, c) => s + c.m, 0);
  return m > 0 ? (100 * cs.reduce((s, c) => s + c.n, 0)) / m : 0;
}

const round1 = (x: number) => Math.round(x * 10) / 10;

export function scoreDimension(cs: Contribution[], opts: { draws?: number; seed?: number } = {}): AxisScore {
  if (!cs.length) return { score: null, ci: null, nItems: 0, nEff: 0, established: false };
  const sm = cs.reduce((s, c) => s + c.m, 0);
  const sm2 = cs.reduce((s, c) => s + c.m * c.m, 0);
  const nEff = (sm * sm) / sm2;
  const score = ratio(cs);
  const draws = opts.draws ?? BOOTSTRAP_DRAWS;
  let ci: [number, number] | null = null;
  if (draws > 0) {
    const rng = mulberry32(opts.seed ?? 20270418);
    const samples: number[] = [];
    for (let b = 0; b < draws; b++) {
      const resample: Contribution[] = [];
      for (let i = 0; i < cs.length; i++) resample.push(cs[Math.floor(rng() * cs.length)]!);
      samples.push(ratio(resample));
    }
    samples.sort((x, y) => x - y);
    ci = [round1(samples[Math.floor(0.025 * draws)]!), round1(samples[Math.min(draws - 1, Math.ceil(0.975 * draws) - 1)]!)];
  }
  return { score: round1(score), ci, nItems: cs.length, nEff: round1(nEff), established: nEff >= MIN_EFFECTIVE_ITEMS };
}

/** Scores de toutes les dimensions (axes et facettes) mesurées par les réponses. */
export function computeScores(questions: Question[], answers: Answers, opts: { draws?: number; seed?: number } = {}): Scores {
  const byDim = new Map<string, Contribution[]>();
  for (const q of questions) for (const [dim, c] of contributions(q, answers[q.id])) add(byDim, dim, c);
  const scores: Scores = {};
  for (const [dim, cs] of byDim) scores[dim as Dimension] = scoreDimension(cs, opts);
  return scores;
}

/** Score brut (sans bootstrap) : utilisé par les simulations. */
export function quickScores(questions: Question[], answers: Answers): Partial<Record<Dimension, number>> {
  const s = computeScores(questions, answers, { draws: 0 });
  return Object.fromEntries(Object.entries(s).map(([k, v]) => [k, v!.score])) as Partial<Record<Dimension, number>>;
}

/** Zone (0..4) d'un score : [−100,−60) [−60,−20) [−20,20] (20,60] (60,100]. */
export function levelOf(score: number): 0 | 1 | 2 | 3 | 4 {
  if (score < -60) return 0;
  if (score < -20) return 1;
  if (score <= 20) return 2;
  if (score <= 60) return 3;
  return 4;
}
