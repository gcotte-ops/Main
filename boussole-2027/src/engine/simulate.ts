import type { Answers, AxisId, Question } from '../domain/schemas';
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
