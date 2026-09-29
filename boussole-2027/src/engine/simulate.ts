import type { Answers, Archetype, AxisId, Candidate, Question } from '../domain/schemas';
import { PRIMARY_AXES } from '../domain/schemas';
import { rankArchetypes, rankCandidates } from './matching';
import type { Scores } from './scoring';
import { gaussian, mulberry32 } from './rng';
import { quickScores } from './scoring';

type Target = Partial<Record<AxisId, number>>;
const clampInt = (x: number) => Math.max(-2, Math.min(2, Math.round(x))) as -2 | -1 | 0 | 1 | 2;

/** Répondant aléatoire uniforme : Likert et dilemmes uniformes sur {−2..+2}, allocations aléatoires. */
export function randomAnswers(questions: Question[], rng: () => number): Answers {
  const a: Answers = {};
  for (const q of questions) {
    if (q.type === 'allocation') {
      const pts = q.options!.map(() => 0);
      for (let i = 0; i < 10; i++) pts[Math.floor(rng() * pts.length)]!++;
      a[q.id] = { kind: 'allocation', points: pts };
    } else a[q.id] = { kind: 'scale', value: clampInt(Math.floor(rng() * 5) - 2) };
  }
  return a;
}

/** Répondant « tout d'accord » : +2 à tous les Likert ; dilemmes sans avis ; allocations uniformes. */
export function allAgreeAnswers(questions: Question[]): Answers {
  const a: Answers = {};
  for (const q of questions) {
    if (q.type === 'likert') a[q.id] = { kind: 'scale', value: 2 };
    else if (q.type === 'dilemma') a[q.id] = { kind: 'scale', value: null };
    else a[q.id] = { kind: 'allocation', points: q.options!.map(() => 1) };
  }
  return a;
}

const proj = (loadings: Partial<Record<AxisId, number>>, t: Target) => {
  let n = 0, d = 0;
  for (const [axis, w] of Object.entries(loadings) as [AxisId, number][]) {
    n += w * ((t[axis] ?? 0) / 100);
    d += Math.abs(w);
  }
  return { n, d };
};

/**
 * Persona : répond selon un vecteur cible (−100..+100) plus un bruit gaussien σ (en points d'échelle).
 * Axes absents du vecteur : position neutre (0). Allocations : parts ∝ exp(3·adhésion de l'option).
 */
export function personaAnswers(questions: Question[], target: Target, rng: () => number, sigma = 0.6): Answers {
  const a: Answers = {};
  for (const q of questions) {
    if (q.type === 'likert') {
      const { n, d } = proj(q.loadings ?? {}, target);
      a[q.id] = { kind: 'scale', value: clampInt(2 * (d ? n / d : 0) + sigma * gaussian(rng)) };
    } else if (q.type === 'dilemma') {
      const A = proj(q.options![0]!.loadings, target);
      const B = proj(q.options![1]!.loadings, target);
      const latent = (B.n - A.n) / Math.max(1e-9, A.d + B.d);
      a[q.id] = { kind: 'scale', value: clampInt(4 * latent + sigma * gaussian(rng)) };
    } else {
      const ws = q.options!.map((o) => Math.exp(3 * proj(o.loadings, target).n + 0.3 * gaussian(rng)));
      const total = ws.reduce((s, x) => s + x, 0);
      a[q.id] = { kind: 'allocation', points: ws.map((x) => Math.round((10 * x) / total)) };
    }
  }
  return a;
}

export interface NeutralityResult { n: number; meanByAxis: Partial<Record<string, number>>; allAgree: Partial<Record<string, number>> }

export function simulateNeutrality(questions: Question[], n = 10_000, seed = 42): NeutralityResult {
  const rng = mulberry32(seed);
  const sums = new Map<string, { s: number; k: number }>();
  for (let i = 0; i < n; i++) {
    const sc = quickScores(questions, randomAnswers(questions, rng));
    for (const [dim, v] of Object.entries(sc)) {
      if (v === null || v === undefined) continue;
      const cur = sums.get(dim) ?? { s: 0, k: 0 };
      cur.s += v; cur.k++;
      sums.set(dim, cur);
    }
  }
  const meanByAxis = Object.fromEntries([...sums].map(([d, { s, k }]) => [d, Math.round((s / k) * 100) / 100]));
  const allAgree = quickScores(questions, allAgreeAnswers(questions)) as Partial<Record<string, number>>;
  return { n, meanByAxis, allAgree };
}

/* --------------------------------------------------------------- Personas */


export interface PersonaResult { id: string; name: string; top3Rate: number; top1Rate: number; runs: number }

const toScores = (q: Partial<Record<string, number | null>>): Scores =>
  Object.fromEntries(Object.entries(q).map(([k, v]) => [k, { score: v ?? null, ci: null, nItems: 1, nEff: 1, established: true }])) as Scores;

export const codedAxes = (c: Candidate) => PRIMARY_AXES.filter((a) => c.positions[a]?.value !== null && c.positions[a]?.value !== undefined);

/** Pour chaque candidat·e avec ≥ minAxes axes codés : part des simulations où il figure dans le top 3. */
export function simulateCandidatePersonas(questions: Question[], candidates: Candidate[], runs = 200, seed = 7, minAxes = 7, sigma = 0.6): PersonaResult[] {
  const rng = mulberry32(seed);
  return candidates.filter((c) => codedAxes(c).length >= minAxes).map((c) => {
    const target = Object.fromEntries(codedAxes(c).map((a) => [a, c.positions[a]!.value!])) as Target;
    let top3 = 0, top1 = 0;
    for (let i = 0; i < runs; i++) {
      const sc = toScores(quickScores(questions, personaAnswers(questions, target, rng, sigma)));
      const user = Object.fromEntries(PRIMARY_AXES.flatMap((a) => (sc[a]?.score != null ? [[a, sc[a]!.score!]] : []))) as Target;
      const ranked = rankCandidates(user, candidates).ranked.map((m) => m.candidate.id);
      const k = ranked.indexOf(c.id);
      if (k >= 0 && k < 3) top3++;
      if (k === 0) top1++;
    }
    return { id: c.id, name: c.name, top3Rate: top3 / runs, top1Rate: top1 / runs, runs };
  });
}

export function simulateArchetypePersonas(questions: Question[], archetypes: Archetype[], runs = 200, seed = 11, sigma = 0.6): PersonaResult[] {
  const rng = mulberry32(seed);
  return archetypes.map((a) => {
    let top3 = 0, top1 = 0;
    for (let i = 0; i < runs; i++) {
      const sc = quickScores(questions, personaAnswers(questions, a.centroid, rng, sigma));
      const user = Object.fromEntries(Object.entries(sc).filter(([k, v]) => !k.includes('.') && v != null)) as Target;
      const ranked = rankArchetypes(user, archetypes).map((m) => m.archetype.id);
      const k = ranked.indexOf(a.id);
      if (k < 3) top3++;
      if (k === 0) top1++;
    }
    return { id: a.id, name: a.name, top3Rate: top3 / runs, top1Rate: top1 / runs, runs };
  });
}
