import { describe, expect, it } from 'vitest';
import type { Answers, Archetype, Candidate, Question, Tension } from '../../src/domain/schemas';
import { computeScores, contributions, levelOf, scoreDimension } from '../../src/engine/scoring';
import { detectBias, findInconsistencies } from '../../src/engine/diagnostics';
import { computeSalience, matchCandidate, rankArchetypes, rankCandidates } from '../../src/engine/matching';
import { computeIndices, detectTensions, opennessIndex } from '../../src/engine/indices';
import { fitPca, project } from '../../src/engine/pca';

const base = { theme: 't', block: 'b', literature: ['keynes'], explanation: 'x'.repeat(60), reversed: false };
const likert = (id: string, loadings: Question['loadings'], extra: Partial<Question> = {}): Question =>
  ({ ...base, id, text: `Énoncé ${id}`, type: 'likert', primaryAxis: Object.keys(loadings!)[0], loadings, ...extra }) as Question;
const scale = (value: -2 | -1 | 0 | 1 | 2 | null, ms?: number) => ({ kind: 'scale' as const, value, ...(ms ? { ms } : {}) });

describe('Formule de score', () => {
  const qs = [likert('Q001', { ECO: 1 }), likert('Q002', { ECO: -1 }), likert('Q003', { ECO: 0.5, ETA: -0.5 })];

  it('S_a = Σ w·r / (2 Σ|w|) × 100', () => {
    const s = computeScores(qs, { Q001: scale(2), Q002: scale(-1), Q003: scale(1) }, { draws: 0 });
    // (2 + 1 + 0,5) / (2 × 2,5) = 0,7
    expect(s.ECO!.score).toBeCloseTo(70, 5);
    expect(s.ETA!.score).toBeCloseTo(-50, 5);
  });

  it('bornes : tout au pôle plus → +100, tout au pôle moins → −100', () => {
    expect(computeScores(qs, { Q001: scale(2), Q002: scale(-2), Q003: scale(2) }, { draws: 0 }).ECO!.score).toBe(100);
    expect(computeScores(qs, { Q001: scale(-2), Q002: scale(2), Q003: scale(-2) }, { draws: 0 }).ECO!.score).toBe(-100);
  });

  it('« sans avis » exclut l\'item (numérateur et dénominateur)', () => {
    const s = computeScores(qs, { Q001: scale(2), Q002: scale(null), Q003: scale(null) }, { draws: 0 });
    expect(s.ECO!.score).toBe(100);
    expect(s.ECO!.nItems).toBe(1);
    expect(s.ETA).toBeUndefined();
  });

  it('les chargements croisés alimentent chaque axe avec leur poids propre', () => {
    const s = computeScores([likert('Q062', { ALT: -0.8, ETA: -0.5, ECO: 0.2 })], { Q062: scale(2) }, { draws: 0 });
    expect(s.ALT!.score).toBe(-100);
    expect(s.ETA!.score).toBe(-100);
    expect(s.ECO!.score).toBe(100);
  });

  it('un dilemme applique l\'option choisie, pondérée par l\'intensité', () => {
    const d = { ...base, id: 'D01', text: 'Dilemme', type: 'dilemma', primaryAxis: 'SEC',
      options: [{ label: 'Punir', loadings: { SEC: -1, GOV: -0.3 } }, { label: 'Innocent', loadings: { SEC: 1, GOV: 0.3 } }] } as Question;
    expect(computeScores([d], { D01: scale(-2) }, { draws: 0 }).SEC!.score).toBe(-100);
    expect(computeScores([d], { D01: scale(1) }, { draws: 0 }).SEC!.score).toBe(50);
    expect(computeScores([d], { D01: scale(0) }, { draws: 0 }).GOV!.score).toBe(0);
  });

  it('une question à choix applique l\'option retenue comme un accord net (n = 2w, m = 2·max|w|)', () => {
    const c = { ...base, id: 'C01', text: 'Régime', type: 'choice', primaryAxis: 'GOV', options: [
      { label: 'Contre-pouvoirs', loadings: { GOV: 0.8 } },
      { label: 'Référendums', loadings: { INS: 0.7, GOV: 0.2 } },
      { label: 'Conseils', loadings: { INS: 0.6, CHG: 0.5 }, facets: { 'REL.laicite': 0.4 } },
      { label: 'Chef', loadings: { GOV: -0.9 } },
    ] } as Question;
    const sc = (index: number | null) => computeScores([c], { C01: { kind: 'choice', index } }, { draws: 0 });
    expect(sc(0).GOV!.score).toBe(88.9); // 100 × 2·0,8 / (2·0,9), arrondi au dixième
    expect(sc(3).GOV!.score).toBe(-100);
    expect(sc(1).INS!.score).toBe(100);
    // Une option qui ne charge pas un axe mesuré par la question le tire vers le centre (n = 0, m > 0).
    expect(sc(0).INS!.score).toBe(0);
    expect(sc(2).CHG!.score).toBe(100);
    expect(sc(2)['REL.laicite']!.score).toBe(100);
    // « Aucune de ces réponses / je ne sais pas » exclut la question.
    expect(sc(null)).toEqual({});
  });

  it('une allocation uniforme est neutre ; tout sur une option donne ±100', () => {
    const a = { ...base, id: 'A01', text: 'Allocation', type: 'allocation', primaryAxis: 'ENV',
      options: [{ label: 'Climat', loadings: { ENV: 0.5 } }, { label: 'Pouvoir d\'achat', loadings: { ENV: -0.5 } }, { label: 'Santé', loadings: {} }] } as Question;
    expect(contributions(a, { kind: 'allocation', points: [4, 4, 4] }).get('ENV')!.n).toBeCloseTo(0, 10);
    expect(computeScores([a], { A01: { kind: 'allocation', points: [10, 0, 0] } }, { draws: 0 }).ENV!.score).toBe(100);
    expect(computeScores([a], { A01: { kind: 'allocation', points: [0, 10, 0] } }, { draws: 0 }).ENV!.score).toBe(-100);
  });

  it('calcule les facettes à partir de facetLoading', () => {
    const q = likert('Q035', { REL: -0.4, ALT: -0.3 }, { facet: 'REL.laicite', facetLoading: 0.8 });
    const s = computeScores([q], { Q035: scale(2) }, { draws: 0 });
    expect(s['REL.laicite']!.score).toBe(100);
    expect(s.REL!.score).toBe(-100);
  });

  it('niveaux : 5 zones', () => {
    expect([-100, -61, -60, -21, -20, 0, 20, 21, 60, 61, 100].map(levelOf)).toEqual([0, 0, 1, 1, 2, 2, 2, 3, 3, 4, 4]);
  });
});

describe('Confiance (n_eff, bootstrap)', () => {
  it('n_eff = nombre d\'items à poids égaux ; « peu établie » sous 4', () => {
    const cs = [1, 2, 3].map((i) => ({ itemId: `Q${i}`, n: 2, m: 2 }));
    expect(scoreDimension(cs, { draws: 0 })).toMatchObject({ nEff: 3, established: false });
    const cs5 = [1, 2, 3, 4, 5].map((i) => ({ itemId: `Q${i}`, n: 2, m: 2 }));
    expect(scoreDimension(cs5, { draws: 0 }).established).toBe(true);
  });
  it('un poids dominant réduit n_eff', () => {
    const cs = [{ itemId: 'a', n: 2, m: 2 }, { itemId: 'b', n: 0.2, m: 0.2 }, { itemId: 'c', n: 0.2, m: 0.2 }];
    expect(scoreDimension(cs, { draws: 0 }).nEff).toBeLessThan(1.5);
  });
  it('l\'IC bootstrap est nul pour des réponses homogènes et large pour des réponses dispersées', () => {
    const same = [1, 2, 3, 4, 5, 6].map((i) => ({ itemId: `${i}`, n: 1, m: 2 }));
    expect(scoreDimension(same).ci).toEqual([50, 50]);
    const mixed = [2, -2, 2, -2, 2, -2].map((n, i) => ({ itemId: `${i}`, n, m: 2 }));
    const r = scoreDimension(mixed);
    expect(r.score).toBe(0);
    expect(r.ci![1] - r.ci![0]).toBeGreaterThan(60);
  });
  it('le bootstrap est déterministe (graine)', () => {
    const cs = [2, -1, 1, 0, 2, -2, 1].map((n, i) => ({ itemId: `${i}`, n, m: 2 }));
    expect(scoreDimension(cs).ci).toEqual(scoreDimension(cs).ci);
  });
});

describe('Cohérence et biais', () => {
  const a = likert('Q010', { ECO: 1 }, { contradicts: ['Q011'], coexistence: 'on peut défendre un principe et refuser un instrument.' });
  const b = likert('Q011', { ECO: 0.8 });
  it('signale deux réponses tirant vers des pôles opposés sur des items de même logique', () => {
    const r = findInconsistencies([a, b], { Q010: scale(2), Q011: scale(-1) });
    expect(r).toHaveLength(1);
    expect(r[0]!.text).toMatch(/Ce n'est pas nécessairement une erreur/);
    expect(findInconsistencies([a, b], { Q010: scale(2), Q011: scale(1) })).toHaveLength(0);
    expect(findInconsistencies([a, b], { Q010: scale(2), Q011: scale(0) })).toHaveLength(0);
  });
  it('signale un même énoncé jugé différemment selon le contexte (blocs appariés)', () => {
    const a = likert('B33a', { GOV: 0.8 }, { group: 'B33', text: 'Les juges devraient pouvoir censurer ses lois.' });
    const b = likert('B34a', { GOV: 0.8 }, { group: 'B34', pair: 'B33a', text: 'Les juges devraient pouvoir censurer ses lois.' });
    const groups = [{ id: 'B33', title: 'Si le gouvernement était du camp opposé', context: 'Imaginez…' }, { id: 'B34', title: 'Si le gouvernement était de votre camp', context: 'Imaginez…' }];
    const r = findInconsistencies([a, b], { B33a: scale(2), B34a: scale(-1) }, 3, groups);
    expect(r).toHaveLength(1);
    expect(r[0]!.text).toMatch(/approuvé « Les juges .* \(si le gouvernement était du camp opposé\).* rejeté le même énoncé .* \(si le gouvernement était de votre camp\)/);
    expect(findInconsistencies([a, b], { B33a: scale(2), B34a: scale(1) }, 3, groups)).toHaveLength(0);
    expect(findInconsistencies([a, b], { B33a: scale(2), B34a: scale(null) }, 3, groups)).toHaveLength(0);
  });
  it('limite à 3 signalements', () => {
    const qs: Question[] = [];
    for (let i = 0; i < 5; i++) qs.push(likert(`Q1${i}0`, { ECO: 1 }, { contradicts: [`Q1${i}1`], coexistence: 'x' }), likert(`Q1${i}1`, { ECO: 1 }));
    const ans: Answers = Object.fromEntries(qs.map((q, k) => [q.id, scale(k % 2 ? -2 : 2)]));
    expect(findInconsistencies(qs, ans)).toHaveLength(3);
  });
  it('détecte l\'acquiescence et les réponses trop rapides', () => {
    const qs = Array.from({ length: 12 }, (_, i) => likert(`Q${100 + i}`, { ECO: i % 2 ? 1 : -1 }));
    const yes: Answers = Object.fromEntries(qs.map((q) => [q.id, scale(2, 800)]));
    expect(detectBias(qs, yes)).toMatchObject({ acquiescence: 'high', tooFast: true });
    const mixed: Answers = Object.fromEntries(qs.map((q, i) => [q.id, scale(i % 2 ? 1 : -1, 4000)]));
    expect(detectBias(qs, mixed)).toMatchObject({ acquiescence: null, tooFast: false });
  });
});

const cand = (id: string, pos: Record<string, [number | null, 'H' | 'M' | 'F']>): Candidate => ({
  id, name: id, party: 'p', bloc: 'b', status: 'Déclaré', statusDetail: '', section: '§3', measureIds: [], sources: ['Fichier 01 §3'], lastUpdated: '2026-09-25',
  positions: Object.fromEntries(Object.entries(pos).map(([a, [value, confidence]]) => [a, { value, confidence, justification: '', sources: [] }])),
});

describe('Correspondances', () => {
  it('saillance : uniforme → 1 ; concentrée → bornée à 2', () => {
    const a = { ...base, id: 'A01', text: 'x', type: 'allocation', primaryAxis: 'ENV',
      options: [{ label: 'Climat', loadings: { ENV: 0.5 } }, { label: 'Sécurité', loadings: { SEC: -0.5 } }] } as Question;
    expect(computeSalience([a], { A01: { kind: 'allocation', points: [5, 5] } })).toEqual({ ENV: 1, SEC: 1 });
    expect(computeSalience([a], { A01: { kind: 'allocation', points: [10, 0] } })).toEqual({ ENV: 2, SEC: 0.5 });
  });

  it('distance pondérée par la confiance, axes null ignorés, normalisée', () => {
    const user = { ECO: 100, ETA: 0 };
    const m = matchCandidate(user, cand('x', { ECO: [100, 'H'], ETA: [100, 'F'], UE: [null, 'F'] }));
    // √((1·0 + 0,3·100²) / 1,3) ≈ 48,0
    expect(m.distance).toBeCloseTo(48, 0);
    expect(m.axesUsed).toBe(2);
    expect(m.rankable).toBe(false);
    expect(m.completeness).toBeCloseTo(0.2);
  });

  it('classe uniquement les candidatures avec ≥ 5 axes et ordonne par distance', () => {
    const axes = ['ECO', 'IDE', 'ENV', 'REL', 'ETA'];
    const user = Object.fromEntries(axes.map((a) => [a, 50]));
    const near = cand('near', Object.fromEntries(axes.map((a) => [a, [50, 'H']])));
    const far = cand('far', Object.fromEntries(axes.map((a) => [a, [-50, 'H']])));
    const thin = cand('thin', { ECO: [50, 'H'] });
    const r = rankCandidates(user, [far, thin, near]);
    expect(r.ranked.map((m) => m.candidate.id)).toEqual(['near', 'far']);
    expect(r.unranked.map((m) => m.candidate.id)).toEqual(['thin']);
    expect(r.ranked[0]!.affinity).toBe(100);
  });

  it('archétypes : le centroïde identique arrive premier', () => {
    const mk = (id: string, centroid: Archetype['centroid']): Archetype => ({ id, name: id, centroid, justification: 'x'.repeat(40), description: 'x'.repeat(80), lineage: ['a', 'b'], counterpoints: ['c'], internalTensions: ['t'] });
    const r = rankArchetypes({ ECO: 80, CUL: -60 }, [mk('a', { ECO: -80, CUL: 60 }), mk('b', { ECO: 80, CUL: -60 })]);
    expect(r[0]!.archetype.id).toBe('b');
    expect(r[0]!.affinity).toBe(100);
    expect(r[1]!.affinity).toBeLessThan(20); // cosinus −1 → 0 ; distance RMS 141 → 15
  });
});

describe('Indices, tensions, carte', () => {
  const s = (v: Record<string, number>) => Object.fromEntries(Object.entries(v).map(([k, score]) => [k, { score, ci: null, nItems: 5, nEff: 5, established: true }]));
  it('indice de souverainisme social marqué quand ECO socialiste et ETA/UE nationaux', () => {
    const idx = computeIndices(s({ ECO: 60, ETA: -70, UE: -50, CUL: 0, ALT: 0, REL: 0 }));
    expect(idx.find((i) => i.id === 'souverainisme-social')).toMatchObject({ value: 60, marked: true });
    expect(idx.find((i) => i.id === 'fusionnisme')!.marked).toBe(false);
  });
  it('l\'indice intersectionnel ignore GEN tant que l\'axe n\'est pas mesuré', () => {
    const idx = computeIndices(s({ ECO: 40, ALT: 80, CUL: 60 }));
    expect(idx.find((i) => i.id === 'intersectionnalite')).toMatchObject({ value: 60, marked: true });
    expect(idx.find((i) => i.id === 'intersectionnalite')!.components.map((c) => c.axis)).toEqual(['ALT', 'ECO', 'CUL']);
  });
  it('règles de tension : conjonction stricte, dimensions non mesurées ignorées', () => {
    const t: Tension[] = [
      { id: 'marche-tradition', title: '', when: [{ axis: 'ECO', op: '<', value: -40 }, { axis: 'CUL', op: '<', value: -40 }], text: '', thinkers: ['michea', 'deneen'] },
      { id: 'tec', title: '', when: [{ axis: 'ENV', op: '>', value: 50 }, { axis: 'TEC', op: '<', value: -30 }], text: '', thinkers: ['a', 'b'] },
    ];
    expect(detectTensions(s({ ECO: -60, CUL: -50, ENV: 80 }), t).map((x) => x.id)).toEqual(['marche-tradition']);
    expect(detectTensions(s({ ECO: -60, CUL: -30 }), t)).toEqual([]);
  });
  it('indice Ouverture–Fermeture : moyenne pondérée, renormalisée si un axe manque', () => {
    expect(opennessIndex({ CUL: 100, ALT: 100, GOV: 100, ETA: 100 })).toBe(100);
    expect(opennessIndex({ CUL: 100, ALT: -100 })).toBe(0);
    expect(opennessIndex({ GOV: 100 })).toBeNull();
  });
  it('ACP : la première composante suit la direction de plus grande variance', () => {
    const rows = [[-100, 0], [-50, 5], [0, -5], [50, 5], [100, 0]];
    const m = fitPca(rows);
    expect(Math.abs(m.components[0][0]!)).toBeGreaterThan(0.99);
    expect(m.explained[0]).toBeGreaterThan(0.95);
    expect(project(m, [100, 0])[0]).toBeCloseTo(100, 0);
  });
});
