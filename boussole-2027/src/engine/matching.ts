import type { Answers, Archetype, AxisId, Candidate, Confidence, Question, Thinker } from '../domain/schemas';
import { PRIMARY_AXES } from '../domain/schemas';
import type { Scores } from './scoring';

/* ------------------------------------------------------------ Saillance */

export const SALIENCE_MIN = 0.5;
export const SALIENCE_MAX = 2;

/**
 * Poids d'importance par axe tiré des allocations (défaut 1). Pour une allocation à k options,
 * l'importance relative d'une option est s_o·k (1 = part moyenne) ; chaque axe chargé par l'option
 * en reçoit une part proportionnelle à |w|. Moyenne sur les allocations, bornée à [0,5 ; 2].
 * Sert uniquement à la correspondance avec les candidat·es, jamais aux scores.
 */
export function computeSalience(questions: Question[], answers: Answers): Partial<Record<AxisId, number>> {
  const acc = new Map<AxisId, { sum: number; weight: number }>();
  for (const q of questions) {
    const a = answers[q.id];
    if (q.type !== 'allocation' || a?.kind !== 'allocation') continue;
    const total = a.points.reduce((s, p) => s + p, 0);
    if (total <= 0) continue;
    const k = q.options!.length;
    q.options!.forEach((o, i) => {
      const rel = ((a.points[i] ?? 0) / total) * k;
      for (const [axis, w] of Object.entries(o.loadings) as [AxisId, number][]) {
        const cur = acc.get(axis) ?? { sum: 0, weight: 0 };
        cur.sum += rel * Math.abs(w);
        cur.weight += Math.abs(w);
        acc.set(axis, cur);
      }
    });
  }
  const out: Partial<Record<AxisId, number>> = {};
  for (const [axis, { sum, weight }] of acc) if (weight > 0) out[axis] = Math.min(SALIENCE_MAX, Math.max(SALIENCE_MIN, sum / weight));
  return out;
}

/* ------------------------------------------------------ Candidat·es */

export const CONFIDENCE_WEIGHT: Record<Confidence, number> = { H: 1, M: 0.6, F: 0.3 };
/** En deçà, la candidature est listée mais non classée (« données insuffisantes »). */
export const MIN_CODED_AXES = 5;

export interface AxisGap { axis: AxisId; user: number; candidate: number; gap: number }
export interface CandidateMatch {
  candidate: Candidate;
  rankable: boolean;
  /** Axes pris en compte (codés chez le candidat et mesurés chez l'utilisateur·ice). */
  axesUsed: number;
  /** Part des 10 axes principaux codés dans le fichier 01. */
  completeness: number;
  /** Écart quadratique moyen pondéré (0..200). */
  distance: number | null;
  /** 100 · (1 − distance / 200). */
  affinity: number | null;
  converge: AxisGap[];
  diverge: AxisGap[];
}

export function userVector(scores: Scores, axes: readonly AxisId[]): Partial<Record<AxisId, number>> {
  const v: Partial<Record<AxisId, number>> = {};
  for (const a of axes) {
    const s = scores[a]?.score;
    if (s !== null && s !== undefined) v[a] = s;
  }
  return v;
}

/**
 * Distance euclidienne pondérée normalisée : d = √( Σ c_a·s_a·(u_a − v_a)² / Σ c_a·s_a ),
 * c_a = confiance du codage (H 1, M 0,6, F 0,3), s_a = saillance. Axes null ignorés.
 * La normalisation évite qu'un candidat peu codé paraisse artificiellement proche.
 */
export function matchCandidate(
  user: Partial<Record<AxisId, number>>,
  c: Candidate,
  salience: Partial<Record<AxisId, number>> = {},
): CandidateMatch {
  let num = 0;
  let den = 0;
  const gaps: AxisGap[] = [];
  let coded = 0;
  for (const axis of PRIMARY_AXES) {
    const p = c.positions[axis];
    if (p?.value === null || p?.value === undefined) continue;
    coded++;
    const u = user[axis];
    if (u === undefined) continue;
    const w = CONFIDENCE_WEIGHT[p.confidence] * (salience[axis] ?? 1);
    num += w * (u - p.value) ** 2;
    den += w;
    gaps.push({ axis, user: u, candidate: p.value, gap: Math.abs(u - p.value) });
  }
  const distance = den > 0 ? Math.sqrt(num / den) : null;
  const sorted = [...gaps].sort((a, b) => a.gap - b.gap);
  return {
    candidate: c,
    rankable: gaps.length >= MIN_CODED_AXES,
    axesUsed: gaps.length,
    completeness: coded / PRIMARY_AXES.length,
    distance: distance === null ? null : Math.round(distance * 10) / 10,
    affinity: distance === null ? null : Math.round(100 * (1 - distance / 200)),
    converge: sorted.slice(0, 3),
    diverge: sorted.slice(-3).reverse(),
  };
}

export function rankCandidates(
  user: Partial<Record<AxisId, number>>,
  candidates: Candidate[],
  salience: Partial<Record<AxisId, number>> = {},
): { ranked: CandidateMatch[]; unranked: CandidateMatch[] } {
  const all = candidates.map((c) => matchCandidate(user, c, salience));
  const ranked = all.filter((m) => m.rankable).sort((a, b) => a.distance! - b.distance!);
  const unranked = all.filter((m) => !m.rankable);
  return { ranked, unranked };
}

/* ------------------------------------------------------------ Archétypes */

export interface ArchetypeMatch { archetype: Archetype; cosine: number; distance: number; affinity: number }

/** Affinité = moitié similarité cosinus ramenée à [0, 1], moitié proximité euclidienne (RMS). */
export function matchArchetype(user: Partial<Record<AxisId, number>>, a: Archetype): ArchetypeMatch {
  let dot = 0, nu = 0, na = 0, sq = 0, n = 0;
  for (const [axis, v] of Object.entries(a.centroid) as [AxisId, number][]) {
    const u = user[axis];
    if (u === undefined) continue;
    dot += u * v; nu += u * u; na += v * v; sq += (u - v) ** 2; n++;
  }
  const cosine = nu > 0 && na > 0 ? dot / Math.sqrt(nu * na) : 0;
  const distance = n ? Math.sqrt(sq / n) : 200;
  const affinity = Math.round(100 * (0.5 * ((1 + cosine) / 2) + 0.5 * (1 - distance / 200)));
  return { archetype: a, cosine: Math.round(cosine * 1000) / 1000, distance: Math.round(distance * 10) / 10, affinity };
}

export function rankArchetypes(user: Partial<Record<AxisId, number>>, archetypes: Archetype[]): ArchetypeMatch[] {
  return archetypes.map((a) => matchArchetype(user, a)).sort((x, y) => y.affinity - x.affinity || x.distance - y.distance);
}

/** Auteur contradicteur : premier auteur non restreint de la filiation de l'archétype le plus éloigné. */
export function pickContradictor(ranked: ArchetypeMatch[], thinkers: Thinker[]): Thinker | undefined {
  const byId = new Map(thinkers.map((t) => [t.id, t]));
  const far = ranked.at(-1)?.archetype;
  return far?.lineage.map((id) => byId.get(id)).find((t) => t && !t.restricted);
}
