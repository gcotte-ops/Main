/**
 * Contrôle du brouillon de questionnaire v2 (blocs de 4 affirmations, choix à 4+ options, 10 répartitions)
 * avec le moteur existant, sans le modifier :
 *  - affirmations et répartitions → contributions() du moteur (Likert / allocation) ;
 *  - choix unique à N options → même formule que les dilemmes : n = 2·w(option choisie), m = 2·max|w|.
 * Usage : npx tsx docs/questionnaire-v2/check-v2.ts
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import archetypes from '../../src/data/archetypes.json';
import candidates from '../../src/data/candidates.json';
import measures from '../../src/data/measures.json';
import thinkers from '../../src/data/thinkers.json';
import { negationCount } from '../../src/domain/lint';
import { ArchetypeSchema, CandidateSchema, PRIMARY_AXES, SECONDARY_AXES, type AxisId, type Question } from '../../src/domain/schemas';
import { rankArchetypes, rankCandidates } from '../../src/engine/matching';
import { gaussian, mulberry32 } from '../../src/engine/rng';
import { contributions, scoreDimension, type Contribution } from '../../src/engine/scoring';

const DIR = import.meta.dirname;
type W = Record<string, number>;
interface Aff { id: string; texte: string; poids: W; mesures?: string[]; factuel?: boolean; paire?: string }
interface Bloc { id: string; titre: string; theme: string; contexte: string; affirmations: Aff[]; auteurs: string[]; explication: string }
interface Choix { id: string; theme: string; question: string; options: { texte: string; poids: W }[]; auteurs: string[]; explication: string }
const load = <T>(f: string) => JSON.parse(readFileSync(join(DIR, f), 'utf8')) as T;
const blocs = [...load<Bloc[]>('blocs-1.json'), ...load<Bloc[]>('blocs-2.json')];
const choix = load<Choix[]>('choix.json');
const reps = load<Choix[]>('repartitions.json');

const AXES = [...PRIMARY_AXES, ...SECONDARY_AXES, 'CHG'] as string[];
const FACETS = ['REL.laicite', 'ENV.nucleaire', 'GMO.intervention', 'GMO.multilateralisme'];
const errors: string[] = [];
const warn: string[] = [];
const th = new Map(thinkers.map((t) => [t.id, t as { restricted?: boolean }]));
const ms = new Set(measures.map((m) => m.id));
const words = (s: string) => s.split(/\s+/).filter((w) => /[\p{L}\d]/u.test(w)).length;
const names = candidates.flatMap((c) => [c.name, c.name.split(' ').slice(1).join(' ')]).filter((n) => n.length >= 4);
const axisOf = (w: W) => Object.entries(w).filter(([k]) => !k.includes('.')).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))[0];

const checkText = (where: string, t: string, max = 30) => {
  if (words(t) > max) errors.push(`${where} : ${words(t)} mots`);
  if (negationCount(t) >= 2) errors.push(`${where} : double négation probable`);
  for (const n of names) if (new RegExp(`(^|[^\\p{L}])${n}([^\\p{L}]|$)`, 'u').test(t)) errors.push(`${where} : nom « ${n} »`);
};
const checkW = (where: string, w: W) => {
  for (const [k, v] of Object.entries(w)) {
    if (!AXES.includes(k) && !FACETS.includes(k)) errors.push(`${where} : axe inconnu ${k}`);
    if (Math.abs(v) > 1) errors.push(`${where} : poids ${v}`);
  }
};
const checkRefs = (where: string, auteurs: string[], mes: string[] = []) => {
  for (const a of auteurs) if (!th.has(a)) errors.push(`${where} : auteur inconnu ${a}`); else if (th.get(a)!.restricted) errors.push(`${where} : auteur restreint ${a}`);
  for (const m of mes) if (!ms.has(m)) errors.push(`${where} : mesure inconnue ${m}`);
};

for (const b of blocs) {
  if (b.affirmations.length !== 4) errors.push(`${b.id} : ${b.affirmations.length} affirmations`);
  checkText(`${b.id} contexte`, b.contexte, 40);
  checkRefs(b.id, b.auteurs);
  for (const a of b.affirmations) { checkText(a.id, a.texte); checkW(a.id, a.poids); checkRefs(a.id, [], a.mesures); }
}
for (const c of [...choix, ...reps]) {
  if (c.options.length < 4) errors.push(`${c.id} : ${c.options.length} options`);
  checkText(`${c.id} question`, c.question, 40);
  checkRefs(c.id, c.auteurs);
  c.options.forEach((o, i) => { checkText(`${c.id}.${i + 1}`, o.texte); checkW(`${c.id}.${i + 1}`, o.poids); });
}

/* ------------------------------------------------ Conversion vers le moteur */
const base = { theme: 't', block: 'b', literature: ['keynes'], explanation: 'x'.repeat(60) };
const likert: Question[] = blocs.flatMap((b) => b.affirmations.map((a) => {
  const loadings = Object.fromEntries(Object.entries(a.poids).filter(([k]) => !k.includes('.')));
  const facet = Object.entries(a.poids).find(([k]) => k.includes('.'));
  const primary = (axisOf(a.poids)?.[0] ?? 'ENV') as AxisId;
  return { ...base, id: 'Q' + a.id, text: a.texte, type: 'likert', primaryAxis: primary, reversed: (loadings[primary] ?? 0) < 0, loadings, ...(facet ? { facet: facet[0], facetLoading: facet[1] } : {}) } as unknown as Question;
}));
const allocs: Question[] = reps.map((r) => ({ ...base, id: r.id, text: r.question, type: 'allocation', primaryAxis: 'ECO', reversed: false,
  options: r.options.map((o) => ({ label: o.texte, loadings: o.poids })) }) as unknown as Question);

type Scale = -2 | -1 | 0 | 1 | 2 | null;
interface Resp { likert: Record<string, Scale>; choix: Record<string, number | null>; alloc: Record<string, number[]> }
function score(r: Resp): Record<string, number | null> {
  const by = new Map<string, Contribution[]>();
  const push = (d: string, c: Contribution) => { if (c.m > 0) by.set(d, [...(by.get(d) ?? []), c]); };
  for (const q of likert) for (const [d, c] of contributions(q, { kind: 'scale', value: r.likert[q.id] ?? null })) push(d, c);
  for (const q of allocs) if (r.alloc[q.id]) for (const [d, c] of contributions(q, { kind: 'allocation', points: r.alloc[q.id]! })) push(d, c);
  for (const c of choix) {
    const k = r.choix[c.id];
    if (k === null || k === undefined) continue;
    const dims = new Set(c.options.flatMap((o) => Object.keys(o.poids)));
    for (const d of dims) {
      const m = 2 * Math.max(...c.options.map((o) => Math.abs(o.poids[d] ?? 0)));
      push(d, { itemId: c.id, n: 2 * (c.options[k]!.poids[d] ?? 0), m });
    }
  }
  return Object.fromEntries([...by].map(([d, cs]) => [d, scoreDimension(cs, { draws: 0 }).score]));
}

/* --------------------------------------------------------------- Statistiques */
const stats: Record<string, { n: number; plus: number; minus: number; sumW: number; sumAbs: number }> = {};
for (const q of likert) for (const [a, w] of Object.entries(q.loadings ?? {})) {
  const s = (stats[a] ??= { n: 0, plus: 0, minus: 0, sumW: 0, sumAbs: 0 });
  s.sumW += w!; s.sumAbs += Math.abs(w!);
  if (a === q.primaryAxis) { s.n++; if (w! > 0) s.plus++; else s.minus++; }
}
console.log('Axe | affirmations (axe principal) | + / − | biais « tout d\'accord »');
for (const a of AXES) {
  const s = stats[a];
  if (!s) { errors.push(`axe ${a} sans affirmation`); continue; }
  const bias = Math.round((100 * s.sumW) / s.sumAbs);
  if (Math.abs(bias) > 25) errors.push(`axe ${a} : biais « tout d'accord » ${bias}`);
  const min = (PRIMARY_AXES as readonly string[]).includes(a) ? 8 : 5;
  if (s.n < min) errors.push(`axe ${a} : ${s.n} affirmations principales (< ${min})`);
  console.log(`${a.padEnd(4)}| ${String(s.n).padStart(3)} | ${s.plus} / ${s.minus} | ${bias}`);
}
const anchored = blocs.flatMap((b) => b.affirmations).filter((a) => a.mesures?.length).length;
const cross = likert.filter((q) => Object.keys(q.loadings ?? {}).length >= 2).length;
console.log(`\n${blocs.length} blocs (${likert.length} affirmations), ${choix.length} choix, ${reps.length} répartitions ; ${anchored} affirmations ancrées dans une mesure ; ${cross} à chargements croisés.`);

// Neutralité : 10 000 répondants aléatoires.
const rng = mulberry32(42);
const acc = new Map<string, { s: number; k: number }>();
for (let i = 0; i < 10000; i++) {
  const r: Resp = { likert: {}, choix: {}, alloc: {} };
  for (const q of likert) r.likert[q.id] = (Math.floor(rng() * 5) - 2) as Scale;
  for (const c of choix) r.choix[c.id] = Math.floor(rng() * c.options.length);
  for (const q of allocs) { const p = q.options!.map(() => 0); for (let k = 0; k < 10; k++) p[Math.floor(rng() * p.length)]!++; r.alloc[q.id] = p; }
  for (const [d, v] of Object.entries(score(r))) if (v !== null) { const x = acc.get(d) ?? { s: 0, k: 0 }; x.s += v; x.k++; acc.set(d, x); }
}
const neutral = [...acc].filter(([d]) => !d.includes('.')).map(([d, { s, k }]) => [d, s / k] as const);
for (const [d, m] of neutral) if (Math.abs(m) > 5) errors.push(`neutralité : ${d} moyenne ${m.toFixed(1)}`);
console.log(`Neutralité (10 000 aléatoires) : ${neutral.map(([d, m]) => `${d} ${m.toFixed(1)}`).join(' · ')}`);

// Personas.
const proj = (w: W, t: W) => { let n = 0, d = 0; for (const [a, x] of Object.entries(w)) { if (a.includes('.')) continue; n += x * ((t[a] ?? 0) / 100); d += Math.abs(x); } return { n, d }; };
function persona(t: W, prng: () => number, sigma = 0.6): Resp {
  const r: Resp = { likert: {}, choix: {}, alloc: {} };
  for (const q of likert) { const { n, d } = proj(q.loadings as W, t); r.likert[q.id] = Math.max(-2, Math.min(2, Math.round(2 * (d ? n / d : 0) + sigma * gaussian(prng)))) as Scale; }
  for (const c of choix) {
    const u = c.options.map((o) => { const { n, d } = proj(o.poids, t); return (d ? n / d : 0) + 0.3 * sigma * gaussian(prng); });
    r.choix[c.id] = u.indexOf(Math.max(...u));
  }
  for (const q of allocs) { const ws = q.options!.map((o) => Math.exp(3 * proj(o.loadings as W, t).n + 0.3 * gaussian(prng))); const tot = ws.reduce((s, x) => s + x, 0); r.alloc[q.id] = ws.map((x) => Math.round((10 * x) / tot)); }
  return r;
}
const as = archetypes.map((a) => ArchetypeSchema.parse(a));
const cs = candidates.map((c) => CandidateSchema.parse(c));
const prng = mulberry32(7);
const res: string[] = [];
for (const a of as) {
  let top3 = 0;
  for (let i = 0; i < 100; i++) {
    const sc = score(persona(a.centroid as W, prng));
    const u = Object.fromEntries(Object.entries(sc).filter(([k, v]) => !k.includes('.') && v !== null)) as W;
    if (rankArchetypes(u, as).slice(0, 3).some((m) => m.archetype.id === a.id)) top3++;
  }
  if (top3 < 90) errors.push(`persona archétype ${a.id} : ${top3} %`);
  res.push(`${a.name} ${top3} %`);
}
console.log(`Personas archétypes (top 3, 100 tirages) : ${res.join(' · ')}`);
const resC: string[] = [];
for (const c of cs) {
  const coded = PRIMARY_AXES.filter((a) => c.positions[a]?.value != null);
  if (coded.length < 7) continue;
  const t = Object.fromEntries(coded.map((a) => [a, c.positions[a]!.value!])) as W;
  let top3 = 0;
  for (let i = 0; i < 100; i++) {
    const sc = score(persona(t, prng));
    const u = Object.fromEntries(PRIMARY_AXES.flatMap((a) => (sc[a] != null ? [[a, sc[a]!]] : []))) as W;
    if (rankCandidates(u, cs).ranked.slice(0, 3).some((m) => m.candidate.id === c.id)) top3++;
  }
  if (top3 < 90) errors.push(`persona candidat ${c.id} : ${top3} %`);
  resC.push(`${c.name} ${top3} %`);
}
console.log(`Personas candidat·es (top 3, 100 tirages) : ${resC.join(' · ')}`);

if (warn.length) console.log(`\nAvertissements :\n- ${warn.join('\n- ')}`);
console.log(errors.length ? `\n${errors.length} erreur(s) :\n- ${errors.join('\n- ')}` : '\nContrôle v2 : OK');
process.exit(errors.length ? 1 : 0);
