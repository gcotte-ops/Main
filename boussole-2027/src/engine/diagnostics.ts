import type { Answers, Question } from '../domain/schemas';

/* ---------------------------------------------------------- Cohérence */

export interface Inconsistency { a: Question; b: Question; strength: number; text: string }

const agreeLabel = (v: number) => (v > 0 ? 'approuvé' : 'rejeté');

/**
 * Paires `contradicts` : deux items qui relèvent de la même logique. Une incohérence est signalée
 * quand les réponses tirent vers des pôles opposés de l'axe principal du premier item (|r| ≥ 1 des deux côtés).
 * Au plus `max` signalements, les plus marqués d'abord, formulés sans jugement.
 */
export function findInconsistencies(questions: Question[], answers: Answers, max = 3): Inconsistency[] {
  const byId = new Map(questions.map((q) => [q.id, q]));
  const found: Inconsistency[] = [];
  for (const a of questions) {
    for (const bid of a.contradicts ?? []) {
      const b = byId.get(bid);
      const ra = answers[a.id];
      const rb = answers[bid];
      if (!b || b.type !== 'likert' || a.type !== 'likert') continue;
      if (ra?.kind !== 'scale' || rb?.kind !== 'scale' || ra.value === null || rb.value === null) continue;
      if (Math.abs(ra.value) < 1 || Math.abs(rb.value) < 1) continue;
      const axis = a.primaryAxis;
      const wa = a.loadings?.[axis] ?? 0;
      const wb = b.loadings?.[axis] ?? 0;
      if (!wa || !wb || Math.sign(wa * ra.value) === Math.sign(wb * rb.value)) continue;
      found.push({
        a, b, strength: Math.abs(ra.value) + Math.abs(rb.value),
        text:
          `Vous avez ${agreeLabel(ra.value)} « ${a.text} » et ${agreeLabel(rb.value)} « ${b.text} », ` +
          `deux énoncés qui relèvent souvent de la même logique. Ce n'est pas une erreur : ${a.coexistence ?? b.coexistence ?? ''}`,
      });
    }
  }
  return found.sort((x, y) => y.strength - x.strength).slice(0, max);
}

/* ------------------------------------------------------ Biais de réponse */

export interface ResponseBias { acquiescence: 'high' | 'low' | null; agreeRate: number | null; tooFast: boolean; meanMs: number | null }

export const FAST_MS = 1500;

/** Acquiescence : part d'accords (r > 0) parmi les Likert répondus > 80 % ou < 20 %. Rapidité : moyenne < 1,5 s. */
export function detectBias(questions: Question[], answers: Answers): ResponseBias {
  let agree = 0;
  let n = 0;
  const times: number[] = [];
  for (const q of questions) {
    const a = answers[q.id];
    if (!a) continue;
    if (a.ms !== undefined) times.push(a.ms);
    if (q.type === 'likert' && a.kind === 'scale' && a.value !== null) {
      n++;
      if (a.value > 0) agree++;
    }
  }
  const agreeRate = n >= 10 ? agree / n : null;
  const meanMs = times.length >= 10 ? times.reduce((s, t) => s + t, 0) / times.length : null;
  return {
    agreeRate,
    acquiescence: agreeRate === null ? null : agreeRate > 0.8 ? 'high' : agreeRate < 0.2 ? 'low' : null,
    meanMs,
    tooFast: meanMs !== null && meanMs < FAST_MS,
  };
}
